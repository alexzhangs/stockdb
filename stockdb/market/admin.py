from django.contrib import admin

from .models import *


# Register your models here.

@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Market._meta.local_fields]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Subject._meta.local_fields if f.name not in ['dpl_rule']]
