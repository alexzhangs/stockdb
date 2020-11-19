# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy_djangoitem import DjangoItem
from tusharepro.models import ApiCategory, Api


class TushareApiCategoryItem(DjangoItem):
    django_model = ApiCategory


class TushareApiItem(DjangoItem):
    django_model = Api
