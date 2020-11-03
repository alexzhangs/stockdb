from django.db import models

from common.models import *


# Create your models here.

class Exchange(models.Model):
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=64)
    area = models.ForeignKey(Area, on_delete=models.RESTRICT, related_name='exchanges')
    currency = models.ForeignKey(Currency, on_delete=models.RESTRICT, related_name='exchanges')
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)


class Market(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.RESTRICT, related_name='markets')
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=32)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)
