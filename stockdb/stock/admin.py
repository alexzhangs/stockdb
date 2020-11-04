from django.contrib import admin

from .models import *


# Register your models here.

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Stock._meta.local_fields]


@admin.register(StockHist)
class StockHistAdmin(admin.ModelAdmin):
    list_display = [f.name for f in StockHist._meta.local_fields]


@admin.register(StockPeriod)
class StockPeriodAdmin(admin.ModelAdmin):
    list_display = [f.name for f in StockPeriod._meta.local_fields]


