from django.contrib import admin
#from django.forms import ModelForm, PasswordInput

from .models import *


# Register your models here.

'''
class AccountForm(ModelForm):
    class Meta:
        model = Account
        fields = ['password', 'token']
        widgets = {
            'password': PasswordInput(),
            'token': PasswordInput(),
        }
'''

@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Config._meta.local_fields]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Account._meta.local_fields if f.name not in ['password','token']]
    #form = AccountForm


@admin.register(ApiCategory)
class ApiCategoryAdmin(admin.ModelAdmin):
    list_display = [f.name for f in ApiCategory._meta.local_fields if f.name not in ['desc']]


@admin.register(Api)
class ApiAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Api._meta.local_fields if f.name not in ['desc']]
