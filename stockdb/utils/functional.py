from django.db import models
from django.core.cache import cache
from django.utils.functional import classproperty

# Create your models here.

class BaseMapper:

    @classmethod
    def clear(cls):
        for name in [k for k, v in cls.__dict__.items() if type(v) is cached_classproperty]:
            cache.delete(name)


class cached_classproperty(classproperty):
    """
    Decorator that converts a method with a single cls argument into a
    property cached on the class.

    A cached class property can be made out of an existing method:
    (e.g. ``url = cached_classproperty(get_absolute_url)``).
    """
    def __init__(self, func, timeout=None):
        self.func = func
        self.timeout = timeout
        self.__doc__ = getattr(func, '__doc__')

    def __get__(self, instance, cls):
        return cache.get_or_set(self.func.__name__, lambda: self.func(cls), self.timeout)


def clean_empty(d):
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [v for v in (clean_empty(v) for v in d) if v]
    return {k: v for k, v in ((k, clean_empty(v)) for k, v in d.items()) if v}


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


