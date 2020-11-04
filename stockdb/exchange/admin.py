from django.contrib import admin

from .models import *


# Register your models here.

@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Exchange._meta.local_fields]


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Market._meta.local_fields]


