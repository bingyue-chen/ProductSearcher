# -*- coding: utf-8 -*-

# Search products from multiple platform
#
# - Retrive product list with search key
# - Retrive product info

import scrapy
import logging
import re
import json


class SearchSpider(scrapy.Spider):
    name = 'search'

    allowed_domains = [
        'etsy.com', 'store.nytimes.com', 'uncommongoods.com',
        'the-citizenry.com', 'findify.io'
    ]

    platform_start_url = {
        'etsy': 'https://www.etsy.com',
        'nytimes': 'https://store.nytimes.com',
        'uncommongoods': 'https://www.uncommongoods.com',
        'citizenry': 'https://www.the-citizenry.com/',
    }

    search_key = None
    search_platforms = ''
    expected_price = '0'
    expected_min_price_ratio = 0.75
    expected_max_price_ratio = 1.25
    expected_min_price = 0
    expected_max_price = 0

    def __init__(self,
                 search_key=None,
                 search_platforms='',
                 expected_price='0',
                 *args,
                 **kwargs):
        super(SearchSpider, self).__init__(*args, **kwargs)

        self.search_key = search_key

        self.search_platforms = []
        if search_platforms:
            self.search_platforms = search_platforms.split(',')

        self.expected_price = 0
        if self.isnumeric(expected_price):
            self.expected_price = float(expected_price)
            self.expected_min_price = self.expected_price * self.expected_min_price_ratio
            self.expected_max_price = self.expected_price * self.expected_max_price_ratio

    def start_requests(self):
        logging.info(self.search_key)
        logging.info(self.search_platforms)
        logging.info(self.platform_start_url)

        for platform in self.search_platforms:
            start_url = self.platform_start_url.get(platform, None)
            start_requests_platform = getattr(self,
                                              'start_requests_' + platform,
                                              None)

            if start_url and start_requests_platform:
                yield scrapy.Request(url=start_url,
                                     callback=start_requests_platform)

    """
    etsy
    """

    def start_requests_etsy(self, response):
        list_url = "https://www.etsy.com/search?q=" + self.search_key + "&ship_to=US"

        if self.expected_price > 0:
            list_url = list_url + "&min=" + str(
                self.expected_min_price) + "&max=" + str(
                    self.expected_max_price)

        req_cookies = self.get_cookie(response.headers.getlist('Set-Cookie'))
        req_cookies['ua'] = '531227642bc86f3b5fd7103a0c0b4fd6'

        yield scrapy.Request(url=list_url,
                             callback=self.parse_list_etsy,
                             cookies=req_cookies,
                             cb_kwargs={
                                 'list_url': list_url,
                                 'page': 0
                             })

    def parse_list_etsy(self, response, list_url, page):

        req_cookies = self.get_cookie(response.headers.getlist('Set-Cookie'))
        req_cookies['ua'] = '531227642bc86f3b5fd7103a0c0b4fd6'

        next_page_disabled = response.css('.wt-action-group__item-container')

        if next_page_disabled:
            next_page_disabled = next_page_disabled[-1].css(
                '.wt-is-disabled').get()

        if not next_page_disabled:
            page = page + 1
            next_list_url = list_url + "&page=" + str(page)

            yield scrapy.Request(url=next_list_url,
                                 callback=self.parse_list_etsy,
                                 cookies=req_cookies,
                                 cb_kwargs={
                                     'list_url': list_url,
                                     'page': page
                                 })

        product_list = response.css('.v2-listing-card')

        for product_element in product_list:
            product = {}

            product['product_name'] = product_element.css(
                'h2::text').get().strip()

            product['product_price'] = product_element.css(
                '.currency-value::text').get().replace(',', '')

            product['product_image'] = product_element.css(
                'img::attr(src)').get()

            if not product['product_image']:
                product['product_image'] = product_element.css(
                    'img::attr(data-src)').get()

            product['product_link'] = product_element.css(
                'a::attr(href)').get().strip()

            if not self.is_filtered(product):
                yield product

    """
    nytimes
    """

    def start_requests_nytimes(self, response):
        list_url = 'https://store.nytimes.com/search?type=product&q=' + self.search_key

        req_cookies = self.get_cookie(response.headers.getlist('Set-Cookie'))

        yield scrapy.Request(url=list_url,
                             callback=self.parse_list_nytimes,
                             cookies=req_cookies,
                             cb_kwargs={
                                 'list_url': list_url,
                                 'page': 0
                             })

    def parse_list_nytimes(self, response, list_url, page):

        req_cookies = self.get_cookie(response.headers.getlist('Set-Cookie'))

        next_page_url = response.css('.next::attr(href)').get()

        if next_page_url:
            page = page + 1
            next_list_url = self.platform_start_url['nytimes'] + next_page_url

            yield scrapy.Request(url=next_list_url,
                                 callback=self.parse_list_nytimes,
                                 cookies=req_cookies,
                                 cb_kwargs={
                                     'list_url': list_url,
                                     'page': page
                                 })

        product_list = response.css('.collection-item-content')

        for product_element in product_list:
            product = {}

            product['product_name'] = product_element.css(
                'h3::text').get().strip()

            product['product_price'] = product_element.css(
                '.red-price::text').get()
            if not product['product_price']:
                product['product_price'] = product_element.css(
                    '.product-price::text').get()

            product['product_price'] = re.findall(r'\d*\.\d+|\d+',
                                                  product['product_price'])[0]

            product['product_image'] = 'https:' + product_element.css(
                'img::attr(src)').get().replace('130x', '330x')

            product['product_link'] = self.platform_start_url[
                'nytimes'] + product_element.css('a::attr(href)').get().strip()

            if not self.is_filtered(product):
                yield product

    """
    uncommongoods
    """

    def start_requests_uncommongoods(self, response):
        list_url = 'https://www.uncommongoods.com/br/search/?q=' + self.search_key + '&account_id=5343&url="/search?q=' + self.search_key + '"&request_type=search&search_type=keyword&fl=pid,title,price,thumb_image,url&rows=60'

        if self.expected_price > 0:
            list_url = list_url + '&fq=sale_price:[' + str(
                int(self.expected_min_price)) + ' TO ' + str(
                    int(self.expected_max_price)) + ']'

        list_url = list_url + '&start='

        yield scrapy.Request(url=list_url + '0',
                             callback=self.parse_list_uncommongoods,
                             cb_kwargs={
                                 'list_url': list_url,
                                 'page': 0
                             })

    def parse_list_uncommongoods(self, response, list_url, page):

        data = json.loads(response.body.decode('UTF-8'))

        num_found = data['response']['numFound']

        if num_found > ((page + 1) * 60):
            page = page + 1
            start = page * 60
            next_list_url = list_url + str(start)

            yield scrapy.Request(url=next_list_url,
                                 callback=self.parse_list_uncommongoods,
                                 cb_kwargs={
                                     'list_url': list_url,
                                     'page': page
                                 })

        for product_data in data['response']['docs']:
            product = {}

            product['product_name'] = product_data['title']
            product['product_price'] = product_data['price']
            product['product_image'] = self.platform_start_url[
                'uncommongoods'] + product_data['thumb_image']
            product['product_link'] = self.platform_start_url[
                'uncommongoods'] + product_data['url']

            if not self.is_filtered(product):
                yield product

    """
    citizenry
    """

    def start_requests_citizenry(self, response):
        list_url = 'https://api-v3.findify.io/v3/search?user[uid]=09chaSnCrVtW2LMn&user[sid]=vBiSMyxGWohWno4c&user[persist]=true&user[exist]=true&limit=100&offset=0&t_client=1574749721693&key=98648189-d258-43a9-9b11-1ad1ebfbb777&q=' + self.search_key

        yield scrapy.Request(url=list_url,
                             callback=self.parse_list_citizenry,
                             cb_kwargs={
                                 'list_url': list_url,
                                 'page': 0
                             })

    def parse_list_citizenry(self, response, list_url, page):

        data = json.loads(response.body.decode('UTF-8'))

        if 'no_result' not in data['meta']:
            for product_data in data['items']:
                product = {}

                product['product_name'] = product_data['title']
                product['product_price'] = product_data['price'][0]
                product['product_image'] = product_data['image_url']
                product['product_link'] = product_data['product_url']

                if not self.is_filtered(product):
                    yield product

    """
    tools
    """

    def get_cookie(self, cookie_list):
        cookies = {}

        for cookie in cookie_list:
            c = cookie.split(b'; ')
            if len(c) > 0:
                c = c[0].split(b'=')
                if len(c) == 2:
                    cookies[c[0]] = c[1]

        return cookies

    def isnumeric(self, str=''):
        return str.replace('.', '1', 1).isdigit()

    def is_filtered(self, product):

        product_price = float(product['product_price'])

        if self.expected_price > 0 and (product_price <
                                        (self.expected_price * 0.8) or
                                        product_price >
                                        (self.expected_price * 1.2)):
            return True

        return False
