# -*- coding: utf-8 -*-
import scrapy
import bs4 as bs
from urllib.parse import quote
from urllib.parse import urljoin
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
            yield scrapy.Request(urljoin(self.urlPrefix,url))

        # get the post urls and collec the info.
        postSubUrls = response.xpath("//a[@class='j_th_tit ']//@href").extract()
        for subrul in postSubUrls:
            url = urljoin(self.urlPrefix,subrul)
            yield scrapy.Request(url,callback=self.parsePost,meta={'url':url})

    def parsePost(self,response):
        l = ItemLoader(item=TiebaItem(),response=response)
        # 标题
        title = response.xpath("//div[@class='core_title_wrap_bright clearfix']//text()")
        if title:
            title = title.extract()[0]
        else:
            title = response.xpath("//div[@class='core_title core_title_theme_bright']//text()").extract()[0]
                                              
        # 链接
        l.add_value("link",response.meta['url'])
        l.add_value("title",title)
        # 跟帖用户
        l.add_xpath("replyUsers","//div[@class='p_postlist']/div/attribute::data-field")
        # 跟帖内容
        replyContent = response.xpath("//div[@class='d_post_content j_d_post_content  clearfix']//text()")
        if replyContent:
            replyContent = replyContent.extract()
        else:
            replyContent = response.xpath("//div[@class='d_post_content j_d_post_content ']//text()").extract()
        l.add_value("replyContent",replyContent)
        yield l.load_item()

    def start_requests(self):
        tiebaname = "湖南商学院"
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