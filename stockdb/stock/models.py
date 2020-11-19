from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils.functional import classproperty
from datetime import datetime
from collections import defaultdict

from common.models import *
from firm.models import *
from market.models import *


# Create your models here.

# refer to:
#   * https://en.wikipedia.org/wiki/International_Securities_Identification_Number
class Stock(models.Model):
    code = models.CharField(max_length=32, unique=True,
        help_text='The unique code given in this application.')
    native_code = models.CharField(max_length=16,
        help_text='The ticker symbol given by the local exchange/market.')
    isin = models.CharField(max_length=12, null=True, blank=True,
    tushare_code = models.CharField(max_length=12, null=True, blank=True, db_index=True)
        help_text='International Securities Identification Number, ISO 6166, https://en.wikipedia.org/wiki/International_Securities_Identification_Number.')
    name = models.CharField(max_length=32)
    firm = models.ForeignKey(Firm, on_delete=models.SET_NULL, null=True, blank=True)
    market = models.ForeignKey(Market, to_field='code', on_delete=models.DO_NOTHING, related_name='stocks')
    subject = models.ForeignKey(Subject, to_field='code', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='stocks')
    total_num = models.IntegerField()
    tradable_num = models.IntegerField()
    status = models.CharField(max_length=16) # Normal,Suspended
    is_listed = models.BooleanField()
    dt_listed = models.DateField()
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
    period = models.ForeignKey(Period, to_field='code', on_delete=models.DO_NOTHING)
    pre_close = models.DecimalField(max_digits=8, decimal_places=2)
    open = models.DecimalField(max_digits=8, decimal_places=2)
    close = models.DecimalField(max_digits=8, decimal_places=2)
    high = models.DecimalField(max_digits=8, decimal_places=2)
    low = models.DecimalField(max_digits=8, decimal_places=2)
    change = models.DecimalField(max_digits=8, decimal_places=2)
    percent = models.DecimalField(max_digits=8, decimal_places=2)
    volume = models.DecimalField(max_digits=8, decimal_places=2)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
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
