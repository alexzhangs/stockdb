from django.db import models

from market.models import *
from index.models import *
from stock.models import *


# Create your models here.

# refer to:
#   * https://zh.wikipedia.org/wiki/上海证券交易所综合股价指数
#   * https://zh.wikipedia.org/wiki/深圳证券交易所成份股价指数
#   * https://zh.wikipedia.org/wiki/恒生指數
#   * https://zh.wikipedia.org/wiki/道琼斯工业平均指数
#   * https://zh.wikipedia.org/wiki/納斯達克綜合指數
#   * https://zh.wikipedia.org/wiki/富時集團
#   * https://www.ftserussell.com/index
#   * https://zh.wikipedia.org/wiki/美元指数
#   * https://zh.wikipedia.org/wiki/國際證券識別碼
#   * https://www.marketwatch.com/tools/quotes/lookup.asp
class Index(models.Model):
    code = models.CharField(max_length=16, unique=True)
    native_code = models.CharField(max_length=16, null=True, blank=True)
    isin = models.CharField(max_length=12, null=True, blank=True)
    name = models.CharField(max_length=32)
    formula = models.CharField(max_length=512, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.RESTRICT, related_name='indexes')
    market = models.ForeignKey(Market, to_field='code', null=True, blank=True, on_delete=models.RESTRICT, related_name='indexes')
    subject = models.ForeignKey(Subject, to_field='code', null=True, blank=True, on_delete=models.RESTRICT, related_name='indexes')
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class IndexStockRef(models.Model):
    index = models.ForeignKey(Index, on_delete=models.RESTRICT, related_name='stocks')
    stock = models.ForeignKey(Stock, on_delete=models.RESTRICT, related_name='indexes')
    weight = models.DecimalField(max_digits=3, decimal_places=2)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)
