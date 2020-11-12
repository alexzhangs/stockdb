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


class Category(models.Model):
    name = models.CharField(max_length=32)
    level = models.SmallIntegerField(help_text='Started with level 1.')
    parent = models.ForeignKey('Category', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='subs')
    desc = models.CharField('Description', max_length=32, null=True, blank=True)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    def __str__(self):
        return self.name


class Api(models.Model):
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=32)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='apis')
    desc = models.CharField('Description', max_length=32, null=True, blank=True)
    credit = models.IntegerField(default=0)
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    def __str__(self):
        return '%s (%s)' % (self.name, self.code)


class Tushare():
    pass
