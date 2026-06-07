from collections import defaultdict
from stock.models import StockPeriod
import timeit
PERIOD = 'DAILY'

timeit.timeit(foo, number=1)
timeit.timeit(bar, number=1)


# 1000: 0.15119249399992896
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.filter(period_id=PERIOD)
    return objs

# 1000: 0.23517805799997404
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.filter(period_id=PERIOD).values('date', 'stock_id')
    return objs

# 1000: 0.28294745800002374
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.values('period_id', 'date', 'stock_id').filter(period_id=PERIOD)
    return objs



# 1000: 0.15859691800005749
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.filter(period_id=PERIOD).distinct('date')
    return objs

# 1000: 0.1828097009999965
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.distinct('period_id', 'date').filter(period_id=PERIOD)
    return objs

# 1000: 0.2483127750000449
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.values('period_id', 'date').distinct().filter(period_id=PERIOD)
    return objs

# 1000: 0.25179073100002825
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.values('period_id', 'date').filter(period_id=PERIOD).distinct()
    return objs



# 1: can't wait
def foo():
    synced_by_date = defaultdict(list)
    objs = list(StockPeriod.objects.filter(period_id=PERIOD))
    return objs

# 1: can't wait
def foo():
    synced_by_date = defaultdict(list)
    objs = list(StockPeriod.objects.filter(period_id=PERIOD).values('date', 'stock_id'))
    return objs



# 1: django.db.utils.NotSupportedError: DISTINCT ON fields is not supported by this database backend
def foo():
    synced_by_date = defaultdict(list)
    objs = list(StockPeriod.objects.filter(period_id=PERIOD).distinct('date'))
    return objs



# 1: 627.473486551
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.filter(period_id=PERIOD)
    for obj in objs: synced_by_date[obj.date.strftime('%Y%m%d')].append(obj.stock_id)
    return synced_by_date

# 1: 119.57670069600022
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.filter(period_id=PERIOD).values('date', 'stock_id')
    for obj in objs: synced_by_date[obj['date'].strftime('%Y%m%d')].append(obj['stock_id'])
    return synced_by_date



# 1: 441.2283700590001
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.filter(period_id=PERIOD).values('date').distinct()
    for obj in objs:
        sps = StockPeriod.objects.filter(date=obj['date'])
        synced_by_date[obj['date'].strftime('%Y%m%d')].extend([sp.stock_id for sp in sps])
    return synced_by_date

# 1: 142.30274747099975
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.filter(period_id=PERIOD).values('date').distinct()
    for obj in objs:
        sps = StockPeriod.objects.filter(period_id=PERIOD, date=obj['date']).values('stock_id')
        synced_by_date[obj['date'].strftime('%Y%m%d')].extend([sp['stock_id'] for sp in sps])
    return synced_by_date



# 1: 138.09729896
def foo():
    synced_by_date = defaultdict(list)
    objs = StockPeriod.objects.filter(period_id=PERIOD).values('date').distinct()
    for obj in objs:
        sps = StockPeriod.objects.filter(period_id=PERIOD, date=obj['date']).values_list('stock_id', flat=True)
        synced_by_date[obj['date'].strftime('%Y%m%d')].extend(sps)
    return synced_by_date



# 1: 6.696967330999996
def bar():
    StockPeriod.Mapper.clear()
    return StockPeriod.Mapper.period_and_market_to_dates




def foo():
    return [Stock.objects.get(tushare_code=x).code for x in Stock.objects.all().values_list('tushare_code', flat=True)]
def bar():
    return [Stock.Mapper.tushare_code_to_code.get(x) for x in Stock.objects.all().values_list('tushare_code', flat=True)]

timeit.timeit(foo, number=3)
13.935992435000117
timeit.timeit(bar, number=3)
0.04944842399982008
