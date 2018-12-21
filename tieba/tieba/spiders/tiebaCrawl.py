# -*- coding: utf-8 -*-
import scrapy
import bs4 as bs
from urllib.parse import quote
import urllib.request
import codecs
from tieba.items import TiebaItem
from scrapy.contrib.loader import ItemLoader

class TiebacrawlSpider(scrapy.Spider):
    name = 'tiebaCrawl'
    allowed_domains = ['tieba.baidu.com']

    def parse(self, response):
        l = ItemLoader(item=TiebaItem(),response=response)
        l.add_xpath("summarys","//a[@class='j_th_tit ']//text()")
        l.add_xpath("links",'//a[@class="j_th_tit "]//@href')
        return l.load_item()

    def getBBSUrl(self,keyword,index):
        encodeKeyword = quote(keyword)
        urlprefix = 'http://tieba.baidu.com/f?kw='
        urlend = '&ie=utf-8&pn='
        if(index == 0):
            pageUrl = urlprefix+encodeKeyword+urlend+str(0)
            yield pageUrl
        else:
            for i in range(index):
                offset = i*50
                pageUrl = urlprefix+encodeKeyword+urlend + str(offset)
                yield pageUrl

    def start_requests(self):
        self.logger.info("START:")
        for url in self.getBBSUrl("守望先锋",10):
           yield self.make_requests_from_url(url)