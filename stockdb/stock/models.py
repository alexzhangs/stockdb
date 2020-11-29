import time
import pandas
from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils.functional import classproperty
from datetime import datetime
from collections import defaultdict

from common.models import Currency, Region, Industry, Period
from firm.models import Firm
from market.models import Market, Subject
from tusharepro.models import Api as TushareApi


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
        skipped = []

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
    amount = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
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
                    cls._period_and_market_to_dates[obj['pm']].append(obj['date'].strftime('%Y%m%d'))
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
                    result[obj['date'].strftime('%Y%m%d')][obj['stock__tushare_code']] = obj['pk']
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
                    result[obj['date'].strftime('%Y%m%d')][obj['stock__market_id']].append(obj['stock__tushare_code'])
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
                tc_df = tc_api.call(fields='cal_date', end_date=datetime.today().strftime('%Y%m%d'), is_open=1)

                result = {}
                for tc_index, tc_row in tc_df.iterrows():
                    sp_api_kwargs['trade_date'] = tc_row['cal_date']
                    # Call daily trade data API
                    sp_df = sp_api.call(**sp_api_kwargs)

                    # add new column to df
                    sp_df['market'] = [Stock.Mapper.tushare_code_to_market.get(x) for x in sp_df.ts_code]

                    result[tc_row['cal_date']] = sp_df.groupby('market')['ts_code'].apply(list).to_dict()
                cls._api_daily_trade_date_to_market_to_ts_code = result
            return cls._api_daily_trade_date_to_market_to_ts_code

    @classmethod
    def sync_daily_from_tushare(cls, market=None, start_date=None, end_date=None, stock_codes=None, clear_mapper=True):
        '''
        PARAMS:
            * market:       Sync the market only.
                            If None, sync all: XSHG, XSHE for now.
            * start_date:   Sync starts from the date, example: 19901231.
                            If None, sync starts from the latest existing date.
                            If an existing date is not found, sync starts from the earliest date.
            * end_date:     Sync ends to the date, example: 19991231.
                            If None, sync ends to today.
            * stock_codes:  Sync the stocks only, example: ['XSHG000001', 'XSHG000002'].
                            If None, sync all the stocks matching the other conditions.
            * clear_mapper: [True|False] Clear used mappers before sync if set True.
        TODO:
            * bulk insert&update
            * trade date timezone
        '''

        PERIOD = 'DAILY'
        MARKETS = ['XSHG', 'XSHE']

        print('%s: %s: sync started with args: %s' % (datetime.now(), PERIOD, locals()))

        tc_api = TushareApi.objects.get(code='trade_cal')
        tc_api.set_token()
        tc_api_kwargs = dict(fields='cal_date', is_open=1)

        sp_api = TushareApi.objects.get(code=PERIOD.lower())
        sp_api.set_token()
        sp_api_kwargs = dict(fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount')
        stock_codes = [x for x in stock_codes if x is not None]
        if stock_codes:
            sp_api_kwargs['ts_code'] = ','.join(stock_codes)

        # Clear Mappers before sync
        if clear_mapper:
            for mapper_cls in [cls, Market, Stock]: mapper_cls.Mapper.clear()

        created_cnt, updated_cnt = 0, 0
        skipped, failed = [], []

        for mcode in ([market] if market else MARKETS):
            print('%s: %s: looping market %s' % (datetime.now(), PERIOD, mcode))

            m_created_cnt, m_updated_cnt = 0, 0
            m_skipped, m_failed = [], []

            acronym = Market.Mapper.code_to_acronym.get(mcode)
            pm = '-'.join([PERIOD, mcode])

            start_date_str = start_date or ((cls.Mapper.period_and_market_to_dates.get(pm) or [None])[-1])
            end_date_str = end_date or datetime.today().strftime('%Y%m%d')

            tc_api_kwargs.update({'exchange': acronym, 'start_date': start_date_str, 'end_date': end_date_str})

            # Call trade calendar API
            tc_df = tc_api.call(**tc_api_kwargs)

            for tc_index, tc_row in tc_df.iterrows():
                tc_date_str = tc_row['cal_date']
                tc_date = datetime.strptime(tc_date_str, '%Y%m%d').date()
                print('%s: %s: looping market %s for date %s' % (datetime.now(), PERIOD, mcode, tc_date))

                tc_created_cnt, tc_updated_cnt = 0, 0
                tc_skipped, tc_failed = [], []
                try_update = True if tc_date_str in (cls.Mapper.period_and_market_to_dates.get(pm) or []) else False

                sp_api_kwargs['trade_date'] = tc_date_str

                # Call daily trade data API
                sp_df = sp_api.call(**sp_api_kwargs)

                for sp_index, sp_row in sp_df.iterrows():
                    if sp_row['ts_code'] not in (Market.Mapper.code_to_stock_tushare_code.get(mcode) or []):
                        continue

                    stock_code = Stock.Mapper.tushare_code_to_code.get(sp_row['ts_code'])
                    if not stock_code:
                        tc_skipped.append(sp_row['ts_code'])
                        continue

                    sp = {
                        'stock_id': stock_code,
                        'market_id': mcode,
                        'period_id': PERIOD,
                        'date': tc_date,
                        'pre_close': sp_row['pre_close'],
                        'open': sp_row['open'],
                        'close': sp_row['close'],
                        'high': sp_row['high'],
                        'low': sp_row['low'],
                        'change': sp_row['change'],
                        'percent': sp_row['pct_chg'],
                        'volume': sp_row['vol'],
                        'amount': sp_row['amount']
                    }

                    try:
                        if try_update:
                            obj, created = cls.objects.update_or_create(stock_id=stock_code, period_id=PERIOD, date=tc_date, defaults=sp)
                            tc_created_cnt += int(created)
                            tc_updated_cnt += int(not(created))
                        else:
                            obj = cls.objects.create(**sp)
                            tc_created_cnt += 1
                    except Exception as e:
                        tc_failed.append([sp_row['ts_code'], tc_date_str])
                        print(e)
                        print(sp)

                print('%s: %s: looping market %s for date %s, ended, created %s, updated: %s, skipped: %s %s, failed: %s %s'
                      % (datetime.now(), PERIOD, mcode, tc_date, tc_created_cnt, tc_updated_cnt, len(tc_skipped), str(tc_skipped), len(tc_failed), str(tc_failed)))
                m_created_cnt += tc_created_cnt
                m_updated_cnt += tc_updated_cnt
                m_skipped = list(set(m_skipped + tc_skipped))
                m_failed += tc_failed

            print('%s: %s: looping market %s, ended, created %s, updated: %s, skipped: %s %s, failed: %s %s'
                  % (datetime.now(), PERIOD, mcode, m_created_cnt, m_updated_cnt, len(m_skipped), str(m_skipped), len(m_failed), str(m_failed)))
            created_cnt += m_created_cnt
            updated_cnt += m_updated_cnt
            skipped = list(set(skipped + m_skipped))
            failed += m_failed

        print('%s: %s: sync ended, created %s, updated: %s, skipped: %s %s, failed: %s %s'
              % (datetime.now(), PERIOD, created_cnt, updated_cnt, len(skipped), str(skipped), len(failed), str(failed)))

    @classmethod
    def checksum_daily_from_tushare(cls, sync=False, remove=False, clear_mapper=True):
        '''
        PARAMS:
            * sync:         [True|False] Sync the missing local data if set True.
            * remove:       [True|False] Remove the extra local data if set True.
            * clear_mapper: [True|False] Clear used mappers before sync if set True.
        '''

        PERIOD = 'DAILY'
        MARKETS = ['XSHG', 'XSHE']

        print('%s: %s: checksum started with args: %s' % (datetime.now(), PERIOD, locals()))

        # Clear Mappers before sync
        if clear_mapper:
            for mapper_cls in [cls, Stock]: mapper_cls.Mapper.clear()

        ## 1. Check remote data
        print('%s: %s: checksum getting remote data' % (datetime.now(), PERIOD))

        remote_by_date = cls.Mapper.api_daily_trade_date_to_ts_code

        ## 2. Check local data
        print('%s: %s: checksum getting local data' % (datetime.now(), PERIOD))

        objs = StockPeriod.objects.filter(period_id=PERIOD, market_id__in=MARKETS, stock__tushare_code__isnull=False).annotate(
            date_str=models.Func(
                models.F('date'), models.Value('%Y%m%d'), function='DATE_FORMAT', output_field=models.CharField()
            )).values_list('date_str', 'stock__tushare_code')
        sp_df = pandas.DataFrame.from_records(objs, columns=['trade_date', 'ts_code'])

        local_by_date = sp_df.groupby('trade_date')['ts_code'].apply(list).to_dict()

        ## 3. Calculate delta between remote and local data
        print('%s: %s: checksum calculating delta between remote and local data' % (datetime.now(), PERIOD))

        for vt, v1, v2 in [
            ('local_missing_by_date', 'local_by_date', 'remote_by_date'),
            ('local_extra_by_date', 'remote_by_date', 'local_by_date'),
        ]:
            v1, v2 = locals()[v1], locals()[v2]
            locals()[vt] = {k: list(set(v or []) - set(v1.get(k) or [])) for k, v in v2.items()}
            locals()[vt] = {k: v for k, v in locals()[vt].items() if v}

        ## 4. Output checksum results
        for name, vr in [
            ('missing', 'local_missing_by_date'),
            ('extra', 'local_extra_by_date'),
        ]:
            vr = locals()[vr]
            print('%s: %s: checksum result: %s data (%s): %s' % (
                datetime.now(), PERIOD, name, len(vr.keys()), ','.join(['%s (%s)' % (k, len(vr[k])) for k, v in vr.items()])))

        ## 5. Sync the missing local data
        if sync:
            print('%s: %s: checksum syncing the missing local data' % (datetime.now(), PERIOD))
            for k, v in locals()['local_missing_by_date'].items():
                stocks = [Stock.Mapper.tushare_code_to_code.get(ts_code) for ts_code in v]
                stocks = [x for x in stocks if x is not None]
                cls.sync_daily_from_tushare(
                    start_date=k,
                    end_date=k,
                    stock_codes=stocks,
                    clear_mapper=False
                )

        ## 6. Remove the extra local data
        if remove:
            print('%s: %s: checksum removing the extra local data' % (datetime.now(), PERIOD))
            for k, v in locals()['local_extra_by_date'].items():
                cls.objects.filter(period=PERIOD, date=datetime.strptime(k, '%Y%m%d'), stock__tushare_code__in=v).delete()

        print('%s: %s: checksum ended' % (datetime.now(), PERIOD))

        return (locals()['local_missing_by_date'], locals()['local_extra_by_date'])
