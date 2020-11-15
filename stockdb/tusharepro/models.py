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

    # Construct a list of category instance from website.
    # The pk field was not set for the instance. 
    def from_website(self):
        results = []
        return results

    # Sync category list from website to DB.
    def sync_from_website(self, remove_local=True):
        objs = self.from_website().sort(key=lambda obj: obj.level)

        for obj in objs:
            db_obj = self.get(name=obj.name) or None
            if db_obj: obj.pk = db_obj.pk
            if obj.parent: obj.parent.refresh_from_db()
            obj.save()

        if remove_local:
            self.exclude(name__in=[obj.name for obj in objs]).delete()


class ApiCategory(models.Model):
    name = models.CharField(max_length=32, unique=True)
    level = models.SmallIntegerField(help_text='Started with level 1.')
    parent = models.ForeignKey('ApiCategory', on_delete=models.SET_NULL, null=True, blank=True, related_name='subs')
    desc = models.CharField('Description', max_length=32, null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    objects = CategoryManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'API Category'


class ApiManager(models.Manager):

    # Construct a list of API instance from website.
    # The pk field was not set for the instance.
    def from_website(self):
        results = []
        return results

    # Sync API list from website to DB.
    def sync_from_website(self, remove_local=True):
        objs = self.from_website()

        for obj in objs:
            db_obj = self.get(code=obj.code) or None
            if db_obj: obj.pk = db_obj.pk
            if obj.category: obj.category = Category.objects.get(name=obj.category.name) or obj.category.save()
            obj.save()

        if remove_local:
            self.exclude(code__in=[obj.code for obj in objs]).delete()


class Api(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=32, unique=True)
    category = models.ForeignKey(ApiCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='apis')
    desc = models.CharField('Description', max_length=512, null=True, blank=True)
    credit = models.IntegerField(default=0, null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    objects = ApiManager()

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)

    class Meta:
        verbose_name = 'API'


class Tushare():

    def __init__(self, *args, **kwargs):
        tushare.set_token('e1d688fdb485284402a5240c6436a6455df9885c768cd45f0d21b52d')
        self.tushare = tushare.pro_api()
