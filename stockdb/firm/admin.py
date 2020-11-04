from django.contrib import admin

from .models import *


# Register your models here.

@admin.register(Firm)
class FirmAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Firm._meta.local_fields]


