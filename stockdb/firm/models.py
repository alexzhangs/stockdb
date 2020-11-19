from django.db import models

from common.models import Region, Industry


# Create your models here.

class Firm(models.Model):
    name = models.CharField(max_length=64)
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, related_name='firms')
    industry = models.ForeignKey(Industry, on_delete=models.DO_NOTHING, related_name='firms')
    dt_created = models.DateTimeField('Created', auto_now_add=True)
    dt_updated = models.DateTimeField('Updated', auto_now=True)

    def __str__(self):
        return self.name
