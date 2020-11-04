from django.contrib import admin

from .models import *


# Register your models here.

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Currency._meta.local_fields]


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Area._meta.local_fields]


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Industry._meta.local_fields]


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Period._meta.local_fields]
