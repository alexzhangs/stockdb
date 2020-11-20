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
                cls._tushare_code_to_code = dict((obj.tushare_code, obj.code) for obj in objs)
            return cls._tushare_code_to_code

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)

    @classmethod
    def sync_from_tushare(cls, market=None):
        '''
        PARAMS:
            * market:     Sync the market only.
                          If None, sync all: XSHG, XSHE for now.
        '''

        print('%s: Stock: sync started' % datetime.now())

        api = TushareApi.objects.get(code='stock_basic')
        api.set_token()
        api_kwargs = dict(
            fields='ts_code,symbol,name,area,market,exchange,list_status,list_date,delist_date',
            exchange = Market.Mapper.code_to_acronym.get(market) if market else None
        )

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
    amount = models.DecimalField(max_digits=16, decimal_places=4)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    class Mapper:
        _period_and_market_to_dates = None

        @classproperty
        def period_and_market_to_dates(cls):
            '''
            RETURN:
                {
                    {period__code}-{market__code}: [{stockperiod__date}.strftime('%Y%m%d'), ...],
                    ...
                }
            '''

            if not cls._period_and_market_to_dates:
                cls._period_and_market_to_dates = defaultdict(list)
                # date to string: extra(select={'datestr': "DATE_FORMAT(date, '%%Y%%m%%d')"})
                objs = StockPeriod.objects.values('date', pm=Concat('period', Value('-'), 'market')).distinct()
                for obj in objs:
                    cls._period_and_market_to_dates[obj['pm']].append(obj['date'].strftime('%Y%m%d'))
            return dict(cls._period_and_market_to_dates)

    @classmethod
    def sync_daily_from_tushare(cls, market=None, start_date=None, end_date=None, stock_code=None):
        '''
        PARAMS:
            * market:     Sync the market only.
                          If None, sync all: XSHG, XSHE for now.
            * start_date: Sync starts from the date, example: 19901231.
                          If None, sync starts from the latest existing date.
                          If an existing date is not found, sync starts from the earliest date.
            * end_date:   Sync ends to the date, example: 19991231.
                          If None, sync ends to today.
            * stock_code: Sync the stock only, example: XSHG000001.
                          If None, sync all the stocks matching the other conditions.
        TODO:
            * bulk insert&update
        '''

        PERIOD = 'DAILY'
        MARKETS = ['XSHG', 'XSHE']

        print('%s: %s: sync started' % (datetime.now(), PERIOD))

        tc_api = TushareApi.objects.get(code='trade_cal')
        tc_api.set_token()

        sp_api = TushareApi.objects.get(code=PERIOD.lower())
        sp_api.set_token()
        sp_api_kwargs = dict(fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount')

        created_cnt, updated_cnt = 0, 0
        skipped = []

        for mcode in ([market] if market else MARKETS):
            print('%s: %s: looping market %s' % (datetime.now(), PERIOD, mcode))

            m_created_cnt, m_updated_cnt = 0, 0
            m_skipped = []

            acronym = Market.Mapper.code_to_acronym.get(mcode)
            pm = '-'.join([PERIOD, mcode])

            if not start_date:
                start_date = (StockPeriod.Mapper.period_and_market_to_dates.get(pm) or [None])[-1]
            if not end_date:
                end_date = datetime.today().strftime('%Y%m%d')

            tc_api_kwargs = dict(exchange=acronym, start_date=start_date, end_date=end_date, is_open=1)

            # Call trade calendar API
            tc_df = tc_api.call(**tc_api_kwargs)

            for tc_index, tc_row in tc_df.iterrows():
                tc_date_str = tc_row['cal_date']
                tc_date = datetime.strptime(tc_date_str, '%Y%m%d').date()
                print('%s: %s: looping market %s for date %s' % (datetime.now(), PERIOD, mcode, tc_date))

                tc_created_cnt, tc_updated_cnt = 0, 0
                tc_skipped = []
                try_update = True if tc_date_str in StockPeriod.Mapper.period_and_market_to_dates.get(pm) else False

                sp_api_kwargs['trade_date'] = tc_date_str

                # Call daily trade data API
                sp_df = sp_api.call(**sp_api_kwargs)

                for sp_index, sp_row in sp_df.iterrows():
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
                    if try_update:
                        obj, created = cls.objects.update_or_create(stock_id=stock_code, period_id=PERIOD, date=tc_date, defaults=sp)
                        tc_created_cnt += int(created)
                        tc_updated_cnt += int(not(created))
                    else:
                        obj = cls.objects.create(**sp)
                        tc_created_cnt += 1

                print('%s: %s: looping market %s for date %s, ended, created %s, updated: %s, skipped: %s' % (datetime.now(), PERIOD, mcode, tc_date, tc_created_cnt, tc_updated_cnt, ','.join(tc_skipped)))
                m_created_cnt += tc_created_cnt
                m_updated_cnt += tc_updated_cnt
                m_skipped = list(set(m_skipped + tc_skipped))

            print('%s: %s: looping market %s, ended, created %s, updated: %s, skipped: %s' % (datetime.now(), PERIOD, mcode, m_created_cnt, m_updated_cnt, ','.join(m_skipped)))
            created_cnt += m_created_cnt
            updated_cnt += m_updated_cnt
            skipped = list(set(skipped + m_skipped))

        print('%s: %s: sync ended, created %s, updated: %s, skipped: %s' % (datetime.now(), PERIOD, created_cnt, updated_cnt, ','.join(skipped)))
