from django.db import models

from exchange.models import *
from index.models import *
from stock.models import *


# Create your models here.

class Index(models.Model):
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=32)
    formula = models.CharField(max_length=512)
    exchange = models.ForeignKey(Exchange, null=True, blank=True, on_delete=models.RESTRICT, related_name='indices')
    market = models.ForeignKey(Market, null=True, blank=True, on_delete=models.RESTRICT, related_name='indices')
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)


class IndexStockRef(models.Model):
    index = models.ForeignKey(Index, on_delete=models.RESTRICT, related_name='stocks')
    stock = models.ForeignKey(Stock, on_delete=models.RESTRICT, related_name='indices')
    weight = models.DecimalField(max_digits=3, decimal_places=2)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)
