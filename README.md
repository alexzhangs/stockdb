# stockdb
Stock data collecting and analyzing.

This project is built with Djang, Scrapy, and Pandas. The data is collected through [Tushare.pro](https://tushare.pro) API, a corresponding Tushare.pro user and token should be configured. 

## About Mappers

  * use the process memory cache rather than django cache framework.
  * django cache framework: 2000 times slower than db query with big object transite.
    * memcached.MemcachedCache: fail to save big object, around 980MB, even set -m 2048 -I 1024m.
    * locmem.LocMemCache: slow transite on with big object.
 