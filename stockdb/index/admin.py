from django.contrib import admin

from .models import *


# Register your models here.

@admin.register(Index)
class IndexAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Index._meta.local_fields]


@admin.register(IndexStockRef)
class IndexStockRefAdmin(admin.ModelAdmin):
    list_display = [f.name for f in IndexStockRef._meta.local_fields]


