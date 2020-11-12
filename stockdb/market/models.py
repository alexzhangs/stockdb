from django.db import models

from common.models import *


# Create your models here.

# refer to:
#   * https://www.iso20022.org/market-identifier-codes
#   * https://zh.wikipedia.org/zh-cn/世界證券交易所列表
class Market(models.Model):
    code = models.CharField(max_length=4, unique=True,
        help_text='Market Identifier Code, ISO 10380, https://www.iso20022.org/market-identifier-codes')
    name = models.CharField(max_length=64)
    acronym = models.CharField(max_length=16)
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, related_name='markets')
    currency = models.ForeignKey(Currency, on_delete=models.DO_NOTHING, related_name='markets')
    website = models.CharField(max_length=128, null=True, blank=True)
    dt_opened = models.DateTimeField('Opened')
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    def __str__(self):
        return '%s(%s)' % (self.name, self.code)


# refer to:
#   * https://zh.wikipedia.org/wiki/深圳证券交易所
#   * https://zh.wikipedia.org/wiki/上海證券交易所科創板
#   * https://zh.wikipedia.org/wiki/深圳证券交易所创业板
#   * http://www.szse.cn/certificate/maind/
#   * http://www.szse.cn/certificate/smeboard/
#   * http://www.szse.cn/certificate/secondb/
#   * https://www.szse.cn/aboutus/sse/documents/P020180328483340183866.pdf
class Subject(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=32)
    level = models.SmallIntegerField()
    market = models.ForeignKey(Market, to_field='code', on_delete=models.DO_NOTHING, related_name='subjects')
    parent = models.ForeignKey('Subject', to_field='code', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='subs')
    trans_plus = models.SmallIntegerField(null=True, blank=True,
        help_text='Transaction plus N days')
    dpl_rule = models.CharField(max_length=256, null=True, blank=True,
        help_text='Daily Price Limite Rule, in Python Expression, -1: unlimited')
    dt_opened = models.DateTimeField('Opened', null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class SubjectHist(models.Model):
    Subject = models.ForeignKey(Subject, to_field='code', on_delete=models.DO_NOTHING, related_name='changes')
    dt_started = models.DateTimeField('Started')
    dt_ended = models.DateTimeField('Ended', null=True, blank=True)
    field = models.CharField(max_length=16) # dpl_rule
    old_value = models.CharField(max_length=256, null=True, blank=True)
    new_value = models.CharField(max_length=256)
    dt_announced = models.DateTimeField('Announced', null=True, blank=True)
    reason = models.CharField(max_length=64, null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)
