from django.db import models


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
        pass

    def sync_credit(self):
        pass


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


class Category(models.Model):
    name = models.CharField(max_length=32)
    level = models.SmallIntegerField(help_text='Started with level 1.')
    parent = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='subs')
    desc = models.CharField('Description', max_length=32, null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    objects = CategoryManager()

    def __str__(self):
        return self.name


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
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=32)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='apis')
    desc = models.CharField('Description', max_length=32, null=True, blank=True)
    credit = models.IntegerField(default=0)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    objects = ApiManager()

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class Tushare():
    pass
