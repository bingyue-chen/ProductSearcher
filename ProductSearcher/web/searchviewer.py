# -*- coding: utf-8 -*-

#
# may have been in progress in another thread when fork() was called.
# solution- export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
#

import os, sys
import hashlib
import json

from multiprocessing import Pool
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings as ScrapySettings
from flask import Flask
from flask import request
from flask import render_template
from pytrends.request import TrendReq

# fix ProductSearcher module not found
dir_path = os.path.dirname(os.path.abspath(__file__))
package_path = os.path.abspath(dir_path + '/../../')
sys.path.append(package_path)

from ProductSearcher import settings as ProductSearcherSettings
from ProductSearcher.spiders.search import SearchSpider

app = Flask(__name__)
app.config.from_object('config')


@app.route('/', methods=['GET'])
def viewer():
    return render_template('viewer.html')


@app.route('/search', methods=['GET'])
def search():

    search_key = request.args.get('search_key', '')
    search_platforms = request.args.get('search_platforms',
                                        'etsy,nytimes,uncommongoods')
    expected_price = str(request.args.get('expected_price', '0'))

    file_name = generate_file_name(search_key, search_platforms, expected_price)
    file_path = '/tmp/' + file_name + '.json'

    try:
        if not os.path.exists(file_path):
            with Pool(processes=1) as pool:
                job = pool.apply_async(runspider,
                                       args=(search_key, search_platforms,
                                             expected_price, file_path))

                pool.close()
                pool.join()

                job.wait()

        if os.path.exists(file_path):
            with open(file_path) as items_file:
                return items_file.read()
        else:
            raise RuntimeError(file_path + " not found")
    except:
        return "Something wrong!!", 500


@app.route('/suggest', methods=['GET'])
def suggest():

    search_key = request.args.get('search_key', '')
    trend_client = TrendReq(hl='en-US', tz=360, geo='US')

    trend_client.build_payload([search_key], gprop='froogle')

    suggest_keywords = trend_client.related_queries()

    suggest_search_keywords = []

    if search_key in suggest_keywords:
        for suggest_type in suggest_keywords[search_key]:
            suggest_search_keywords = suggest_search_keywords + suggest_keywords[
                search_key][suggest_type]['query'].values.tolist()

    return json.dumps(suggest_search_keywords)


def runspider(search_key, search_platforms, expected_price, file_path):
    item_count = 300

    settings = ScrapySettings()
    settings.setmodule(ProductSearcherSettings)
    settings.set('FEED_FORMAT', 'json')
    settings.set('FEED_URI', file_path)
    settings.set('CLOSESPIDER_ITEMCOUNT', item_count)
    settings.set('LOG_LEVEL', 'ERROR')

    processes = CrawlerProcess(settings)

    processes.crawl(
        SearchSpider,
        search_key=search_key,
        search_platforms=search_platforms,
        expected_price=expected_price,
    )

    processes.start()


def generate_file_name(search_key, search_platforms, expected_price):

    h_str = search_key.encode('UTF-8') + search_platforms.encode(
        'UTF-8') + expected_price.encode('UTF-8')

    return hashlib.sha256(h_str).hexdigest()


if __name__ == '__main__':

    run_port = 8080
    env_port = os.getenv('FLASK_RUN_PORT')

    if env_port and env_port.isdigit():
        run_port = int(env_port)

    app.run(host="127.0.0.1", port=run_port, threaded=True)
