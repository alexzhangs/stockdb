from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from admin_actions.admin import ActionsModelAdmin

from .models import *


# Register your models here.

@admin.register(Stock)
class StockAdmin(ActionsModelAdmin):
    list_display = [f.name for f in Stock._meta.local_fields]
    actions_list = ('sync_from_tushare', )
    def sync_from_tushare(self, request):
        self.model.sync_from_tushare()
        return redirect(reverse_lazy('admin:stock_stock_changelist'))


@admin.register(StockHist)
class StockHistAdmin(admin.ModelAdmin):
    list_display = [f.name for f in StockHist._meta.local_fields]


@admin.register(StockPeriod)
class StockPeriodAdmin(ActionsModelAdmin):
    list_display = [f.name for f in StockPeriod._meta.local_fields]
    actions_list = ('sync_daily_from_tushare', )
    def sync_daily_from_tushare(self, request):
        self.model.sync_dialy_from_tushare()
        return redirect(reverse_lazy('admin:stock_stockperiod_changelist'))


