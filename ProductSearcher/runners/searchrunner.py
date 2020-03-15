# -*- coding: utf-8 -*-

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ProductSearcher.spiders import search

search_key = 'pillows'
search_platforms = 'etsy,nytimes,uncommongoods,citizenry'
expected_price = '0'
item_count = 100

settings = get_project_settings()
settings.set('FEED_FORMAT', 'csv')
settings.set('FEED_URI', search_key + '.csv')
settings.set('CLOSESPIDER_ITEMCOUNT', item_count)
settings.set('LOG_LEVEL', 'INFO')

process = CrawlerProcess(settings)

process.crawl(search.SearchSpider,
              search_key=search_key,
              search_platforms=search_platforms,
              expected_price=expected_price)

process.start()
