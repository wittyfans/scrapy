# -*- coding: utf-8 -*-
import scrapy
import bs4 as bs
from urllib.parse import quote
from urllib.parse import urljoin
import urllib.request
import codecs
from tieba.items import TiebaItem
from scrapy.contrib.loader import ItemLoader

class TiebacrawlSpider(scrapy.Spider):
    name = 'tiebaCrawl'
    allowed_domains = ['tieba.baidu.com']
    urlPrefix = 'https://tieba.baidu.com'

    def parse(self, response):
        # get the next page info
        nextPageUrls = response.xpath("//a[@class='next pagination-item ']//@href")
        for url in nextPageUrls.extract():
            self.logger.info("=====Now request:{}=====".format(url))
            yield scrapy.Request(urljoin(self.urlPrefix,url))

        # get the post urls and collec the info.
        postSubUrls = response.xpath("//a[@class='j_th_tit ']//@href").extract()
        for subrul in postSubUrls:
            url = urljoin(self.urlPrefix,subrul)
            yield scrapy.Request(url,callback=self.parsePost,meta={'url':url})

    def parsePost(self,response):
        l = ItemLoader(item=TiebaItem(),response=response)
        title = response.xpath("//div[@class='core_title_wrap_bright clearfix']//text()").extract()[0]
        l.add_value("link",response.meta['url'])
        l.add_value("title",title)
        l.add_xpath("replyUsers","//div[@class='d_author']//li[@class='d_name']//a[@class='p_author_name j_user_card']//text()")
        l.add_xpath("replyContent","//div[@class='d_post_content j_d_post_content ']//text()")
        yield l.load_item()

    def start_requests(self):
        tiebaname = "守望先锋"
        self.logger.info(tiebaname)
        encodedUrl = self.encodeUrl(tiebaname)
        self.logger.info("Now request {}".format(encodedUrl))
        yield scrapy.Request(encodedUrl, callback=self.parse)

    def encodeUrl(self,keyword):
        encodeKeyword = quote(keyword)
        urlprefix = 'https://tieba.baidu.com/f?kw='
        urlend = '&ie=utf-8&pn='
        requestUrl = urlprefix+encodeKeyword+urlend+str(0)
        return requestUrl