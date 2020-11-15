# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from crawler.items import TushareApiCategoryItem, TushareApiItem


class TushareItemRelationPipeline:
    def process_item(self, item, spider):
        if isinstance(item, TushareApiCategoryItem) and item.get('parent'):
            item['parent'] = item.django_model.objects.get(name=item['parent']['name'])
        elif isinstance(item, TushareApiItem) and item.get('category'):
            item['category'] = item['category'].django_model.objects.get(name=item['category']['name'])
        else:
            pass

        return item


class TushareItemPersistencePipeline:
    def process_item(self, item, spider):
        if isinstance(item, (TushareApiCategoryItem, TushareApiItem)):
            try:
                instance = item.django_model.objects.get(name=item['name'])
                item.instance.pk = instance.pk
                item.instance.dt_created = instance.dt_created
            except item.django_model.DoesNotExist:
                pass
        else:
            pass

        item.save()
        return item
