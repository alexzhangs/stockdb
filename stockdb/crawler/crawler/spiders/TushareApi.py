import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re

from crawler.items import TushareApiCategoryItem, TushareApiItem
from tusharepro.models import Config


class TushareApiSpider(CrawlSpider):
    name = 'TushareApi'
    scheme = Config.objects.get(code='site_scheme').value
    domain = Config.objects.get(code='site_domain').value
    path = Config.objects.get(code='site_path_for_api_doc').value
    allowed_domains = [domain]
    base_url = '%s://%s' % (scheme, domain)
    start_urls = ['%s%s' % (base_url, path)]

    rules = (
        # Extract links matching 'item.php' and parse them with the spider's method parse_item
        Rule(LinkExtractor(allow=(path + '$', )), callback='parse_api_category'),
    )

    def parse_api_category(self, response, level=1, parent=None):
        rows = response.xpath('//div[@id="jstree"]/ul/li[@class]') if level == 1 else response.xpath('ul/li[@class]')
        if rows: # category nodes found
            self.logger.debug('found %s category nodes at level %s' % (len(rows), level))
            for row in rows:
                item = self.parse_api_category_item(row, level, parent)
                yield item
                for item in self.parse_api_category(row, level+1, item):
                    yield item
        else: # try API nodes
            for item in self.parse_api(response, parent):
                yield item

    def parse_api_category_item(self, response, level, parent):
        item = TushareApiCategoryItem()
        item['name'] = response.xpath('a/text()').get()
        item['level'] = level
        item['parent'] = parent
        item['desc'] = None #TODO
        return item

    def parse_api(self, response, category):
        rows = response.xpath('ul/li')
        for row in rows:
            link = self.base_url + row.xpath('a/attribute::href').get()
            yield scrapy.Request(
                url=link,
                callback=self.parse_api_item,
                cb_kwargs={'category': category})

    def parse_api_item(self, response, category):
        prefix = '//div[@class="document"]/div[@class[contains(., "content")]]'
        item = TushareApiItem()
        item['name'] = response.xpath(prefix + '/h2/text()').get()
        item['category'] = category
        item['code'] = response.xpath(prefix + '/p[child::text()]').re_first(r'[^：]*接口[^：]*：([^<>]*)')
        item['desc'] = response.xpath(prefix + '/p/text()').re_first(r'描述：(.*)')
        item['credit'] = response.xpath(prefix + '/p/text()').re_first(r'(\d+)积分')
        return item
