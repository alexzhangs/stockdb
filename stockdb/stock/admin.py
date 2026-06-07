from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from admin_actions.admin import ActionsModelAdmin

from .models import *


# Register your models here.

from django.core.paginator import Paginator
from django.db import connection, transaction, OperationalError


class TimeLimitedPaginator(Paginator):
    """
    Paginator that enforced a timeout on the count operation.
    When the timeout is reached a "fake" large value is returned instead,
    Why does this hack exist? On every admin list view, Django issues a
    COUNT on the full queryset. There is no simple workaround. On big tables,
    this COUNT is extremely slow and makes things unbearable. This solution
    is what we came up with.
    """

    @cached_property
    def count(self):
        # We set the timeout in a db transaction to prevent it from
        # affecting other transactions.
        with transaction.atomic(), connection.cursor() as cursor:
            # timeout in milliseconds
            cursor.execute('SET SESSION MAX_EXECUTION_TIME=200;')
            try:
                count = super().count
            except OperationalError:
                count = 9999999999
            finally:
                # reset to default timeout
                cursor.execute('SET SESSION MAX_EXECUTION_TIME=0;')
            return count


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
    show_full_result_count = False
    paginator = TimeLimitedPaginator

    def sync_daily_from_tushare(self, request):
        self.model.sync_dialy_from_tushare()
        return redirect(reverse_lazy('admin:stock_stockperiod_changelist'))
