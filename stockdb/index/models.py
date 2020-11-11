from django.db import models

from market.models import *
from index.models import *
from stock.models import *


# Create your models here.

class Index(models.Model):
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=32)
    formula = models.CharField(max_length=512, null=True, blank=True)
    market = models.ForeignKey(Market, to_field='code', null=True, blank=True, on_delete=models.RESTRICT, related_name='indices')
    subject = models.ForeignKey(Subject, to_field='code', null=True, blank=True, on_delete=models.RESTRICT, related_name='indices')
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class IndexStockRef(models.Model):
    index = models.ForeignKey(Index, on_delete=models.RESTRICT, related_name='stocks')
    stock = models.ForeignKey(Stock, on_delete=models.RESTRICT, related_name='indices')
    weight = models.DecimalField(max_digits=3, decimal_places=2)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)
