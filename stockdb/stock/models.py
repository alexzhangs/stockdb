import time
import pandas
from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils.functional import classproperty
from datetime import datetime, date
from collections import defaultdict

from common.models import Currency, Region, Industry, Period
from firm.models import Firm
from market.models import Market, Subject
from tusharepro.models import Api as TushareApi


def date_to_str(d):
    if isinstance(d, (str, type(None))):
        return d
    if isinstance(d, (date, datetime)):
        return date.strftime(d, '%Y%m%d')
    else:
        raise TypeError('requires `%s`, but received a `%s`.' % ((date, datetime), type(d)))

def str_to_date(d):
    if isinstance(d, str):
        return datetime.strptime(d, '%Y%m%d').date()
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, (date, type(None))):
        return d
    else:
        raise TypeError('requires `%s` in format `%%Y%%m%%d`, but received a `%s`.' % (str, type(d)))

def clean_empty(d):
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [v for v in (clean_empty(v) for v in d) if v]
    return {k: v for k, v in ((k, clean_empty(v)) for k, v in d.items()) if v}

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# Create your models here.

# refer to:
#   * https://en.wikipedia.org/wiki/International_Securities_Identification_Number
class Stock(models.Model):
    code = models.CharField(max_length=32, unique=True,
        help_text='The unique code given in this application.')
    native_code = models.CharField(max_length=16, db_index=True,
        help_text='The ticker symbol given by the local exchange/market.')
    tushare_code = models.CharField(max_length=12, null=True, blank=True, db_index=True)
    isin = models.CharField(max_length=12, null=True, blank=True, db_index=True,
        help_text='International Securities Identification Number, ISO 6166, https://en.wikipedia.org/wiki/International_Securities_Identification_Number.')
    name = models.CharField(max_length=32)
    firm = models.ForeignKey(Firm, on_delete=models.SET_NULL, null=True, blank=True)
    market = models.ForeignKey(Market, to_field='code', on_delete=models.DO_NOTHING, related_name='stocks')
    subject = models.ForeignKey(Subject, to_field='code', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='stocks')
    total_num = models.IntegerField(null=True, blank=True)
    tradable_num = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, db_index=True) # L: listed, D: Delisted, P: Suspended
    is_listed = models.BooleanField(db_index=True)
    dt_listed = models.DateField(db_index=True)
    dt_delisted = models.DateField(null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    class Mapper:
        _tushare_code_to_code = None
        _code_to_tushare_code = None
        _code_to_market = None
        _tushare_code_to_market = None

        @classmethod
        def clear(cls):
            cls._tushare_code_to_code = None
            cls._code_to_tushare_code = None
            cls._code_to_market = None
            cls._tushare_code_to_market = None

        @classproperty
        def tushare_code_to_code(cls):
            '''
            RETURN:
                {
                    {tushare_code}: {code},
                    ...
                }
            '''

            if not cls._tushare_code_to_code:
                objs = Stock.objects.filter(tushare_code__isnull=False)
                cls._tushare_code_to_code = {obj.tushare_code: obj.code for obj in objs}
            return cls._tushare_code_to_code

        @classproperty
        def code_to_tushare_code(cls):
            '''
            RETURN:
                {
                    {code}: {tushare_code},
                    ...
                }
            '''

            if not cls._code_to_tushare_code:
                objs = Stock.objects.filter(tushare_code__isnull=False)
                cls._code_to_tushare_code = {obj.code: obj.tushare_code for obj in objs}
            return cls._code_to_tushare_code

        @classproperty
        def code_to_market(cls):
            '''
            RETURN:
                {
                    {code}: {market_code},
                    ...
                }
            '''

            if not cls._code_to_market:
                objs = Stock.objects.all()
                cls._code_to_market = {obj.code: obj.market_id for obj in objs}
            return cls._code_to_market

        @classproperty
        def tushare_code_to_market(cls):
            '''
            RETURN:
                {
                    {tushare_code}: {market_code},
                    ...
                }
            '''

            if not cls._tushare_code_to_market:
                objs = Stock.objects.filter(tushare_code__isnull=False)
                cls._tushare_code_to_market = {obj.tushare_code: obj.market_id for obj in objs}
            return cls._tushare_code_to_market

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)

    @classmethod
    def sync_from_tushare(cls, market=None, clear_mapper=True):
        '''
        PARAMS:
            * market:       Sync the market only.
                            If None, sync all: XSHG, XSHE for now.
            * clear_mapper: [True|False] Clear used mappers before sync if set True.
        '''

        print('%s: Stock: sync started with args: %s' % (datetime.now(), locals()))

        api = TushareApi.objects.get(code='stock_basic')
        api.set_token()
        api_kwargs = dict(
            fields='ts_code,symbol,name,area,market,exchange,list_status,list_date,delist_date',
            exchange = Market.Mapper.code_to_acronym.get(market) if market else None
        )

        # Clear Mappers before sync
        if clear_mapper:
            for mapper_cls in [Market, Subject]: mapper_cls.Mapper.clear()

        created_cnt, updated_cnt = 0, 0

        for status in ['D','L','P']:
            print('%s: Stock: looping status %s' % (datetime.now(), status))

            api_kwargs['list_status'] = status

            # Call stock list API
            df = api.call(**api_kwargs)

            s_created_cnt, s_updated_cnt = 0, 0

            for index, row in df.iterrows():
                market_code = Market.Mapper.acronym_to_code.get(row['exchange'])
                code = market_code + row['symbol']
                subject_code = Subject.Mapper.tushare_exchange_and_market_to_code.get(
                    '-'.join([row['exchange'], row['market']])) if row['market'] else None

                stock = {
                    'code': code,
                    'native_code': row['symbol'],
                    'tushare_code': row['ts_code'],
                    'name': row['name'],
                    'market_id': market_code,
                    'subject_id': subject_code,
                    'status': row['list_status'],
                    'is_listed': True if row['list_status'] in ['L', 'P'] else False,
                    'dt_listed': datetime.strptime(row['list_date'], '%Y%m%d').date(),
                    'dt_delisted': datetime.strptime(row['delist_date'], '%Y%m%d').date() if row['delist_date'] else None
                }
                obj, created = cls.objects.update_or_create(code=code, defaults=stock)
                s_created_cnt += int(created)
                s_updated_cnt += int(not(created))

            print('%s: Stock: looping status %s, ended, created: %s, updated, %s' % (datetime.now(), status, s_created_cnt, s_updated_cnt))
            created_cnt += s_created_cnt
            updated_cnt += s_updated_cnt

        print('%s: Stock: sync ended, created: %s, updated: %s' % (datetime.now(), created_cnt, updated_cnt))


class StockHist(models.Model):
    stock = models.ForeignKey(Stock, to_field='code', on_delete=models.DO_NOTHING, related_name='changes')
    dt_started = models.DateTimeField()
    dt_ended = models.DateTimeField()
    field = models.CharField(max_length=16) # name, status, total_num, tradable_num
    old_value = models.CharField(max_length=32)
    new_value = models.CharField(max_length=32)
    dt_announced = models.DateTimeField()
    reason = models.CharField(max_length=64)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)


class StockPeriod(models.Model):
    stock = models.ForeignKey(Stock, to_field='code', on_delete=models.DO_NOTHING, related_name='periods')
    market = models.ForeignKey(Market, to_field='code', on_delete=models.DO_NOTHING, related_name='stockperiods')
    period = models.ForeignKey(Period, to_field='code', on_delete=models.DO_NOTHING)
    date = models.DateField(db_index=True)
    pre_close = models.DecimalField(max_digits=8, decimal_places=2)
    open = models.DecimalField(max_digits=8, decimal_places=2)
    close = models.DecimalField(max_digits=8, decimal_places=2)
    high = models.DecimalField(max_digits=8, decimal_places=2)
    low = models.DecimalField(max_digits=8, decimal_places=2)
    change = models.DecimalField(max_digits=8, decimal_places=2)
    percent = models.DecimalField(max_digits=8, decimal_places=2)
    volume = models.DecimalField(max_digits=16, decimal_places=2)
    amount = models.DecimalField(max_digits=16, decimal_places=4)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    class Meta:
        unique_together = ('stock', 'period', 'date')

    class Mapper:
        _period_and_market_to_dates = None
        _daily_date_to_stock_tushare_code_to_pk = None
        _daily_date_to_market_to_stock_tushare_code = None
        _api_daily_trade_date_to_market_to_ts_code = None

        @classmethod
        def clear(cls):
            cls._period_and_market_to_dates = None
            cls._daily_date_to_stock_tushare_code_to_pk = None
            cls._daily_date_to_market_to_stock_tushare_code = None
            cls._api_daily_trade_date_to_market_to_ts_code = None

        @classproperty
        def period_and_market_to_dates(cls):
            '''
            RETURN:
                {
                    {period_id}-{market_id}: [{date}.strftime('%Y%m%d'), ...].sort(),
                    ...
                }
            '''

            if not cls._period_and_market_to_dates:
                cls._period_and_market_to_dates = defaultdict(list)
                objs = StockPeriod.objects.values('date', pm=Concat('period', Value('-'), 'market')).distinct().order_by('date')
                for obj in objs:
                    cls._period_and_market_to_dates[obj['pm']].append(date_to_str(obj['date']))
            return cls._period_and_market_to_dates

        @classproperty
        def daily_date_to_stock_tushare_code_to_pk(cls):
            '''
            RETURN:
                {
                    {date}.strftime('%Y%m%d'): {
                        {stock__tushare_code}: {pk},
                        ...
                    },
                    ...
                }
            '''

            PERIOD = 'DAILY'
            if not cls._daily_date_to_stock_tushare_code_to_pk:
                objs = StockPeriod.objects.filter(period_id=PERIOD, stock__tushare_code__isnull=False).values('date', 'stock__tushare_code', 'pk')
                result = defaultdict(dict)
                for obj in objs:
                    result[date_to_str(obj['date'])][obj['stock__tushare_code']] = obj['pk']
                cls._daily_date_to_stock_tushare_code_to_pk = result
            return cls._daily_date_to_stock_tushare_code_to_pk

        @classproperty
        def daily_date_to_market_to_stock_tushare_code(cls):
            '''
            RETURN:
                {
                    {date}.strftime('%Y%m%d'): {
                        {market_id}: [{stock__tushare_code}, ...],
                        ...
                    },
                    ...
                }
            '''

            PERIOD = 'DAILY'
            if not cls._daily_date_to_market_to_stock_tushare_code:
                objs = StockPeriod.objects.filter(period_id=PERIOD, stock__tushare_code__isnull=False).values('date', 'stock__market_id', 'stock__tushare_code')
                result = defaultdict(lambda: defaultdict(list))
                for obj in objs:
                    result[date_to_str(obj['date'])][obj['stock__market_id']].append(obj['stock__tushare_code'])
                cls._daily_date_to_market_to_stock_tushare_code = result
            return cls._daily_date_to_market_to_stock_tushare_code

        @classproperty
        def api_daily_trade_date_to_market_to_ts_code(cls):
            '''
            RETURN:
                {
                    {trade_date}: {
                        {market}: [{ts_code}, ...],
                        ...
                    },
                    ...
                }
            '''

            PERIOD = 'DAILY'
            if not cls._api_daily_trade_date_to_market_to_ts_code:
                tc_api = TushareApi.objects.get(code='trade_cal')
                tc_api.set_token()

                sp_api = TushareApi.objects.get(code=PERIOD.lower())
                sp_api.set_token()
                sp_api_kwargs = dict(fields='ts_code')

                # Call trade calendar API
                tc_df = tc_api.call(fields='cal_date', end_date=date_to_str(datetime.today()), is_open=1)

                result = {}
                for tc_index, tc_row in tc_df.iterrows():
                    sp_api_kwargs['trade_date'] = tc_row['cal_date']
                    # Call daily trade data API
                    sp_df = sp_api.call(**sp_api_kwargs)

                    # add new column to df
                    sp_df.insert(loc=0, column='market', value=sp_df.ts_code.apply(Stock.Mapper.tushare_code_to_market.get))
                    # drop rows with empty ts_code or market
                    sp_df.dropna()

                    result[tc_row['cal_date']] = sp_df.groupby('market')['ts_code'].apply(list).to_dict()
                cls._api_daily_trade_date_to_market_to_ts_code = result
            return cls._api_daily_trade_date_to_market_to_ts_code

    @classmethod
    def sync_daily_from_tushare(cls, market, dates=None, start_date=None, end_date=None, stocks=None, clear_mapper=True):
        '''
        PARAMS:
            * market:       The market to sync, example: 'XSHG'.
            * dates:        Sync for the dates, example: '19991231' or ['19991230', '19991231'].
                            If Set, `start_date` and `end_date` are ignored.
            * start_date:   Sync starts from the date, example: 19900101.
                            If None, sync starts from the latest synced date in the appreciated market.
                            If an existing synced date is not found, sync starts from the earliest date.
            * end_date:     Sync ends to the date, example: 19991231.
                            If None, sync ends to today.
            * stocks:       Sync the stocks only, example: 'XSHG000001' or ['XSHG000001', 'XSHG000002'].
                            If None, sync all the stocks of the market.
            * clear_mapper: [True|False] Clear used mappers before to sync if set True.
        TODO:
            * custom cached class property, to replace mappers
            * trade date timezone
        '''

        PERIOD = 'DAILY'

        print('%s: %s: sync started with args: %s' % (datetime.now(), PERIOD, locals()))

        ## Inner Functions
        def get_start_date(market, stocks=[]):
            if stocks:
                try:
                    d = cls.objects.filter(period_id=PERIOD, market_id=market, stock_id__in=stocks).latest('date').date
                except cls.DoesNotExist:
                    d = None
            else:
                d = (cls.Mapper.period_and_market_to_dates.get('-'.join([PERIOD, market])) or [None])[-1]

            return date_to_str(d) if d is not None else d

        def get_end_date():
            return date_to_str(datetime.today())

        def get_dates(market, start_date, end_date):
            if start_date and start_date == end_date:
                results = [start_date]
            else:
                api = TushareApi.objects.get(code='trade_cal')
                api.set_token()

                # Call trade calendar API
                df = api.call(
                    fields='cal_date',
                    exchange=Market.Mapper.code_to_acronym.get(market),
                    start_date=start_date,
                    end_date=end_date,
                    is_open=1)
                results = df['cal_date'].to_list()

            return results

        def save_sp(market, trade_date, df, create=True, update=False):
            PERIOD = 'DAILY'
            print('%s: %s: save StockPeriod with args: %s' % (datetime.now(), PERIOD, locals()))

            created, updated, skipped = [], [], []
            if len(df) == 0:
                return len(created), len(updated), skipped

            # add column market_id to df
            df.insert(loc=0, column='market_id', value=df.ts_code.apply(Stock.Mapper.tushare_code_to_market.get))

            # filter df rows with appreciated market
            df = df[df.market_id == market].copy()

            # add column pk to df if found one in DB
            df.insert(loc=0, column='pk', value=df.apply(
                lambda row: StockPeriod.Mapper.daily_date_to_stock_tushare_code_to_pk.get(trade_date, {}).get(
                    row.ts_code), axis=1))

            # rename columns name to map to DB model
            df.rename(columns={'trade_date': 'date', 'pct_chg': 'percent', 'vol': 'volume'},
                      inplace=True)

            # update column date in df
            df.loc[:, 'date'] = str_to_date(trade_date)

            # add columns to df
            df.insert(loc=1, column='stock_id', value=df.ts_code.apply(Stock.Mapper.tushare_code_to_code.get))
            df.insert(loc=3, column='period_id', value=PERIOD)

            # remove unused columns
            df.drop(['ts_code'], axis=1, inplace=True)

            if create:
                # filter df rows for creating
                cdf = df[df.pk.isnull()].copy()
                if len(cdf):
                    cdf.drop(['pk'], axis=1, inplace=True)
                    cleaned_cdf = cdf.dropna()
                    skipped.extend(cdf[~cdf.index.isin(cleaned_cdf.index)].to_dict('records'))

                    # bulk create
                    created = cls.objects.bulk_create(
                        [cls(**d) for d in cleaned_cdf.to_dict('records')],
                        batch_size=5000)

            if update:
                # filter df rows for updating
                udf = df[~df.pk.isnull()]
                if len(udf):
                    cleaned_udf = udf.dropna()
                    skipped.extend(udf[~udf.index.isin(cleaned_udf.index)].to_dict('records'))

                    # bulk update
                    updated = cls.objects.bulk_update(
                        [cls(**d) for d in udf.to_dict('records')],
                        ['pre_close', 'open', 'close', 'high', 'low', 'change', 'percent', 'volume', 'amount'],
                        batch_size=5000)

            print('%s: %s: save StockPeriod ended, created: %s, updated: %s, skipped: %s'
                  % (datetime.now(), PERIOD, len(created), len(updated), len(skipped)))

            return len(created), len(updated), skipped

        def sync(market, dates, stocks=[]):
            api = TushareApi.objects.get(code=PERIOD.lower())
            api.set_token()
            api_kwargs = dict(fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount')
            if stocks:
                stocks = [Stock.Mapper.code_to_tushare_code.get(x) for x in stocks if x]

            created_cnt, updated_cnt, skipped = 0, 0, []
            for d in dates:
                api_kwargs['trade_date'] = d

                for chunked_stocks in chunks(stocks, 100):
                    api_kwargs['ts_code'] = ','.join(clean_empty(chunked_stocks))
                    # Call daily trade data API
                    df = api.call(**api_kwargs)

                    if len(df):
                        i, j, m = save_sp(market, d, df)
                        created_cnt += i
                        updated_cnt += j
                        skipped.extend(m)

            return created_cnt, updated_cnt, skipped
        ## Inner Functions End

        ## Parameters
        if isinstance(dates, (list, tuple, set)):
            dates = [date_to_str(x) for x in dates if x is not None]
        else:
            dates = [date_to_str(dates)] if dates is not None else []

        if isinstance(stocks, (list, tuple, set)):
            stocks = [x for x in stocks if x is not None]
        else:
            stocks = [stocks] if stocks is not None else []
        ## Parameters End

        ## Main

        # Clear Mappers before sync
        if clear_mapper:
            for mapper_cls in [cls, Market, Stock]: mapper_cls.Mapper.clear()

        if not dates:
            start_date = date_to_str(start_date) if start_date else get_start_date(market, stocks)
            end_date = date_to_str(end_date) if end_date else get_end_date()
            dates = get_dates(market, start_date, end_date)

        created_cnt, updated_cnt, skipped = sync(market, dates, stocks)

        print('%s: %s: sync ended, created: %s, updated: %s, skipped: %s %s'
              % (datetime.now(), PERIOD, created_cnt, updated_cnt, len(skipped), skipped))

        return created_cnt, updated_cnt, skipped

    @classmethod
    def checksum_daily_from_tushare(cls, sync=False, remove=False, clear_mapper=True):
        '''
        PARAMS:
            * sync:         [True|False] Sync the missing local data if set True.
            * remove:       [True|False] Remove the extra local data if set True.
            * clear_mapper: [True|False] Clear used mappers before sync if set True.
        '''

        PERIOD = 'DAILY'

        print('%s: %s: checksum started with args: %s' % (datetime.now(), PERIOD, locals()))

        # Clear Mappers before sync
        if clear_mapper:
            for mapper_cls in [cls, Stock]: mapper_cls.Mapper.clear()

        ## 1. Check remote data
        print('%s: %s: checksum getting remote data' % (datetime.now(), PERIOD))

        remote_by_date = cls.Mapper.api_daily_trade_date_to_market_to_ts_code

        ## 2. Check local data
        print('%s: %s: checksum getting local data' % (datetime.now(), PERIOD))

        local_by_date = cls.Mapper.daily_date_to_market_to_stock_tushare_code

        ## 3. Calculate delta between remote and local data
        print('%s: %s: checksum calculating delta between remote and local data' % (datetime.now(), PERIOD))

        for vt, v1, v2 in [
            ('local_missing_by_date', 'local_by_date', 'remote_by_date'),
            ('local_extra_by_date', 'remote_by_date', 'local_by_date'),
        ]:
            v1, v2 = locals()[v1], locals()[v2]
            locals()[vt] = {
                dt: {m: list(set(codes) - set((v1.get(dt) or {}).get(m) or [])) for m, codes in val.items() if codes}
                for dt, val in v2.items() if val}
            locals()[vt] = clean_empty(locals()[vt])

        ## 4. Output checksum results
        for name, vr in [
            ('missing', 'local_missing_by_date'),
            ('extra', 'local_extra_by_date'),
        ]:
            vr = locals()[vr]
            print('%s: %s: checksum result: %s data (%s): %s' % (datetime.now(), PERIOD, name, len(vr.keys()), vr))

        ## 5. Sync the missing local data
        if sync:
            print('%s: %s: checksum syncing the missing local data' % (datetime.now(), PERIOD))
            created_cnt, updated_cnt, skipped = 0, 0, []
            for dt, val in locals()['local_missing_by_date'].items():
                for m, codes in val.items():
                    stocks = [Stock.Mapper.tushare_code_to_code.get(ts_code) for ts_code in codes]
                    i, j, m = cls.sync_daily_from_tushare(
                        market=m,
                        dates=dt,
                        stocks=clean_empty(stocks),
                        clear_mapper=False
                    )
                    created_cnt += i
                    updated_cnt += j
                    skipped.extend(m)

            print('%s: %s: checksum sync ended, created: %s, updated: %s, skipped: %s %s'
                  % (datetime.now(), PERIOD, created_cnt, updated_cnt, len(skipped), skipped))

        ## 6. Remove the extra local data
        if remove:
            print('%s: %s: checksum removing the extra local data' % (datetime.now(), PERIOD))
            for dt, val in locals()['local_extra_by_date'].items():
                for m, codes in val.items():
                    cls.objects.filter(period=PERIOD, date=str_to_date(dt), stock__tushare_code__in=codes).delete()

        print('%s: %s: checksum ended' % (datetime.now(), PERIOD))

        return (locals()['local_missing_by_date'], locals()['local_extra_by_date'])
