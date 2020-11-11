from django.db import models

from common.models import *
from firm.models import *
from market.models import *


# Create your models here.

class Stock(models.Model):
    code = models.CharField(max_length=32, unique=True)
    inner_code = models.CharField(max_length=16)
    name = models.CharField(max_length=32)
    firm = models.ForeignKey(Firm, on_delete=models.SET_NULL, null=True, blank=True)
    market = models.ForeignKey(Market, to_field='code', on_delete=models.RESTRICT, related_name='stocks')
    subject = models.ForeignKey(Subject, to_field='code', on_delete=models.RESTRICT, null=True, blank=True, related_name='stocks')
    total_num = models.IntegerField()
    tradable_num = models.IntegerField()
    status = models.CharField(max_length=16) # Normal,Suspended
    is_listed = models.BooleanField()
    dt_listed = models.DateField()
    dt_delisted = models.DateField(null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class StockHist(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.RESTRICT, related_name='changes')
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
    stock = models.ForeignKey(Stock, on_delete=models.RESTRICT, related_name='periods')
    period = models.ForeignKey(Period, on_delete=models.RESTRICT)
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
