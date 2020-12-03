from django.db import models
from django.core.cache import cache
from django.utils.functional import classproperty

# Create your models here.

class BaseMapper:

    @classmethod
    def clear(cls):
        """
        Clear the cached_classproperty under the Mapper.
        """
        for f in [v for k, v in cls.__dict__.items() if type(v) is cached_classproperty]:
            if hasattr(cls, f.cache_key):
                delattr(cls, f.cache_key)


class cached_classproperty(classproperty):
    """
    Decorator that converts a method with a single cls argument into a
    property cached on the class.

    A cached class property can be made out of an existing method:
    (e.g. ``url = cached_classproperty(get_absolute_url)``).
    """
    @property
    def cache_key(self):
        return '_' + self.fget.__name__

    def __get__(self, instance, cls):
        if not hasattr(cls, self.cache_key):
            setattr(cls, self.cache_key, self.fget(cls))
        return getattr(cls, self.cache_key)


def clean_empty(d):
    """
    Clean empty node in nested Dict or List.
    """
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [v for v in (clean_empty(v) for v in d) if v]
    return {k: v for k, v in ((k, clean_empty(v)) for k, v in d.items()) if v}


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


