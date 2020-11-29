import time
from datetime import datetime

from django.db import models
import tushare


# Create your models here.

class Config(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=32)
    value = models.CharField(max_length=256, null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class Account(models.Model):
    user_id = models.CharField(max_length=16)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32, null=True, blank=True)
    token = models.CharField(max_length=64, null=True, blank=True)
    credit = models.IntegerField(null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    def __str__(self):
        return '%s (%s)' % (self.username, self.user_id)

    def authenticate(self):
        pass #TODO

    def sync_credit(self):
        pass #TODO


class CategoryManager(models.Manager):

    # Sync category list from website to DB.
    def sync_from_website(self):
        pass


class ApiCategory(models.Model):
    name = models.CharField(max_length=32, unique=True)
    level = models.SmallIntegerField(help_text='Started with level 1.')
    parent = models.ForeignKey('ApiCategory', on_delete=models.SET_NULL, null=True, blank=True, related_name='subs')
    desc = models.CharField('Description', max_length=32, null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    objects = CategoryManager()

    class Meta:
        verbose_name = 'API Category'

    def __str__(self):
        return self.name


class ApiManager(models.Manager):

    # Sync API and category list from website to DB.
    def sync_from_website(self, remove_local=True):
        pass


class Api(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=32, unique=True)
    category = models.ForeignKey(ApiCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='apis')
    desc = models.CharField('Description', max_length=512, null=True, blank=True)
    credit = models.IntegerField(default=0, null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    objects = ApiManager()

    class Meta:
        verbose_name = 'API'

    class Timer:

        PERIOD = 61

        def __init__(self, api, *args, **kwargs):
            self.api = api
            self.reset()

        def reset(self):
            self.starter = time.time()
            self.counter = 0

        @property
        def elapse(self):
            return int(time.time() - self.starter)

        def count(self, period=PERIOD):
            '''
            PARAMS:
                * API throttling period, in seconds.
            '''

            if self.elapse > period:
                self.reset()

            self.counter += 1

        def hang(self, period=PERIOD):
            '''
            PARAMS:
                * API throttling period, in seconds.
            '''

            left = period - self.elapse
            if left > 0:
                print('%s: %s: WARNING: API has been throttling by server, was called %s times within %s seconds, sleeping %s seconds.' % (
                    datetime.now(), self.api.code, self.counter, self.elapse, left))
                time.sleep(left)

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)

    def __init__(self, *args, **kwargs):
        self.caller = tushare.pro_api()
        self.timer = self.Timer(self)

        super(Api, self).__init__(*args, **kwargs)

    def set_token(self, token=None):
        if token:
            self.caller.__init__(token)
        else:
            self.caller.__init__(Account.objects.first().token)

    def call(self, *args, **kwargs):
        if not self.caller._DataApi__token:
            raise Exception('Set a token first with Api.set_token(self, [token]).')
        else:
            func = getattr(self.caller, self.code)
            while 1:
                try:
                    self.timer.count()
                    return func(*args, **kwargs)
                except:
                    self.timer.hang()
