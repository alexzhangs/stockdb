from django.db import models


# Create your models here.

class Currency(models.Model):
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=64)
    symbol = models.CharField(max_length=8)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)


class Area(models.Model):
    name = models.CharField(max_length=64)
    parent = models.ForeignKey('Area', on_delete=models.RESTRICT, related_name='subs')
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)


class Industry(models.Model):
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=64)
    parent = models.ForeignKey('Industry', on_delete=models.RESTRICT, related_name='subs')
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)


class Period(models.Model):
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=64)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)
