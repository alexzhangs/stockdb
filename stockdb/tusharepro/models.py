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

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)

    def __init__(self, *args, **kwargs):
        self.caller = None

        super(Api, self).__init__(*args, **kwargs)

    def set_token(self, token=None):
        if token:
            self.caller = tushare.pro_api(token)
        else:
            self.caller = tushare.pro_api(Account.objects.first().token)

    def call(self, *args, **kwargs):
        if not self.caller:
            raise Error('Set a token first with Api.set_token(self, [token]).')
        else:
            return getattr(self.caller, self.code)(*args, **kwargs)
