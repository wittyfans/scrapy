# -*- coding: utf-8 -*-
import scrapy
import bs4 as bs
from urllib.parse import quote
import urllib.request
import codecs
from tieba.items import TiebaItem

class TiebacrawlSpider(scrapy.Spider):
    name = 'tiebaCrawl'
    allowed_domains = ['tieba.baidu.com']

    def parse(self, response):
        alltitles = []
        item = TiebaItem()
        titles = response.xpath("//a[@class='j_th_tit ']//text()").extract()
        for title in titles:
            alltitles.append(title)
            self.logger.info(title)
        item["summarys"] = alltitles
        return item

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