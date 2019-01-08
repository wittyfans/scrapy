# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import bs4 as bs
from urllib.parse import quote
from urllib.parse import urljoin
import codecs
from tieba.items import TiebaItem
from scrapy.contrib.loader import ItemLoader


class EasytiebacrawlSpider(CrawlSpider):
    name = 'easytiebaCrawl'
    allowed_domains = ['tieba.baidu.com']
    urlPrefix = 'https://tieba.baidu.com'
    start_urls = ["http://tieba.baidu.com/f?kw=%E6%B9%96%E5%8D%97%E6%B6%89%E5%A4%96%E7%BB%8F%E6%B5%8E%E5%AD%A6%E9%99%A2&ie=utf-8&pn=0"]

    rules = (
        Rule(LinkExtractor(restrict_xpaths="//div[@class='pb_footer']//ul[@class='l_posts_num']//a"),callback='parsepage'),
        Rule(LinkExtractor(restrict_xpaths="//a[@class='j_th_tit ']"),callback='parsePost')
    )

    def parsepage(self, response):
        # get the post urls and collec the info.
        postSubUrls = response.xpath("//a[@class='j_th_tit ']//@href").extract()
        for subrul in postSubUrls:
            self.logger.info("=========Request======={}".format(postSubUrls))
            url = urljoin(self.urlPrefix,subrul)
            yield scrapy.Request(url,callback=self.parsePost)

        # get the next page info
        nextPageUrls = response.xpath("//a[@class='next pagination-item ']//@href")    
        for url in nextPageUrls.extract():
            yield scrapy.Request(urljoin(self.urlPrefix,url),callback=self.parsepage)

    def parsePost(self,response):
        meta = response.meta
        l = ItemLoader(TiebaItem(),response=response)
        # title
        if 'title' in meta:
            title = meta['title']    
        else:
            title = response.xpath("//div[@class='core_title_wrap_bright clearfix']//text()")
            if title:
                title = title.extract()[0]
            else:
                title = response.xpath("//div[@class='core_title core_title_theme_bright']//text()").extract()[0]
            meta['title'] = title
        l.add_value('title',title)
        # link
        l.add_value('link',response.url)
        
        # 跟帖用户
        l.add_xpath("replyUsers","//div[@class='p_postlist']/div/attribute::data-field")
        
        # 跟帖内容
        replyContent = response.xpath("//div[@class='d_post_content j_d_post_content  clearfix']//text()")
        if replyContent:
            replyContent = replyContent.extract()
        else:
            replyContent = response.xpath("//div[@class='d_post_content j_d_post_content ']//text()").extract()
        l.add_value('replyContent',replyContent)
        
        # get the next post info
        nextPages = response.xpath("//div[@class='pb_footer']//ul[@class='l_posts_num']//a//@href")
        if nextPages:
            lastPage = nextPages[-1].extract()
            self.logger.info("LastPage:{}".format(lastPage))
            self.logger.info("ResponseURL:{}".format(response.url))
            if not lastPage in response.url:
                nextPage = response.xpath("//div[@class='pb_footer']//ul[@class='l_posts_num']//a//@href")[-2]
                nextPageUrl = urljoin(self.urlPrefix,nextPage.extract())
                yield scrapy.Request(nextPageUrl,callback=self.parsePost,meta=meta)
        yield l.load_item()