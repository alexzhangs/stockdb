from django.db import models


# Create your models here.

# refer to: https://zh.wikipedia.org/wiki/ISO_4217
class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=32)
    symbol = models.CharField(max_length=8)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)



# Level 2, refer to: https://gist.github.com/richjenks/15b75f1960bc3321e295
# Level 3, refer to: https://zh.wikipedia.org/zh-hans/ISO_3166-1
# Level 4 & 5, partly refer to: https://github.com/adyliu/china_area
class Region(models.Model):
    code = models.CharField(max_length=9, unique=True)
    name = models.CharField(max_length=64)
    level = models.SmallIntegerField()
    parent = models.ForeignKey('Region', to_field='code', on_delete=models.RESTRICT, null=True, blank=True, related_name='subs')
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)


class Industry(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=64)
    level = models.SmallIntegerField()
    parent = models.ForeignKey('Industry', to_field='code', on_delete=models.RESTRICT, null=True, blank=True, related_name='subs')
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)


class Period(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=64)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)
