# # -*- coding: utf-8 -*-
# import scrapy
# from scrapy.linkextractors import LinkExtractor
# from scrapy.spiders import CrawlSpider, Rule
# from scrapy.http import FormRequest

# class LoginSpider(CrawlSpider):
#     name = 'login'
#     allowed_domains = ['http://douban.com']
#     # start_urls = ['http://http://douban.com/']
#     # 将 start_ urls语句替换为 start_ requests()方法。这样做是因为在本例中，我们需要从一些更加定制化的请求开始，而不仅仅是几个 URL。更确切地说就是，我们从该函数中创建并返回一个 FormRequest。

#     def start_requests(self):
#         return [FormRequest(
#             "https://accounts.douban.com/login",
#             formdata = {"form_email":"15580804250","form_password":"908462357tW"}
#         )]
#     rules = (
#         # Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=False),
#         Rule(LinkExtractor(restrict_xpaths="//div[@class='stream-items']"),callback='parse_homepage'),
#     )

#     def parse_homepage(self,response):
#         print("===========================")
#         print("   {}".format(response))

import scrapy
import urllib.request
from scrapy import Request
class DbSpider(scrapy.Spider):
    name = 'doubanlogin'
    allowed_domains = ['douban.com']
    #start_urls = ['http://douban.com/']
    def start_requests(self):#该方法必须返回一个可迭代对象。该对象包含了spider用于爬取的第一个Request。当spider启动爬取并且未制定URL时，该方法被调用。meta参数的作用是传递信息给下一个函数,下面start_requests中键‘cookiejar’是一个特殊的键，scrapy在meta中见到此键后，会自动将cookie传递到要callback的函数中。既然是键(key)，就需要有值(value)与之对应，例子中给了数字1，也可以是其他值，比如任意一个字符串。可以理解为：再次刷新网页时不丢失登陆信息？
        return [Request('https://accounts.douban.com/login?',callback=self.parse,meta={'cookiejar':1})]

    def parse(self, response):
        capt = response.xpath('//div/img[@id="captcha_image"]/@src').extract()#获取验证码地址
        url = 'https://accounts.douban.com/login'
        print(capt)
        if len(capt)>0:#判断是否有验证
            print('有验证码')
            local_path = '/Users/wittyfans/Desktop/scrapy/login_to_douban/login_to_douban/capt.jpeg'
            urllib.request.urlretrieve(capt[0], filename=local_path)#保存验证码到本地
            print('查看本地验证码图片并输入')
            capt_id = response.xpath('//div/input[@name="captcha-id"]/@value').extract()
            captcha_value = input()#验证码
            data = {#均从chrome浏览器检查及查看源码抓包来
                    'form_email': '15580804250',#邮箱账号
                    'form_password': '908462357tW',#密码
                    'captcha-solution': captcha_value,
                    'source':'index_nav',
                    'captcha-id':capt_id,
                    'redir': 'https://www.douban.com/people/80224588/'#登陆成功要返回的link，我们返回主页
                    }
        else:
            print('没有验证码')
            data = {
                    'form_email':'15580804250',#账号
                    'form_password':'908462357tW',#密码
                    'source':'index_nav',
                    'redir':'https://www.douban.com/people/174174633/'
                    }
            print('login...')
        return [#使用Scrapy抓取网页时，如果想要预填充或重写像用户名、用户密码这些表单字段， 可以使用 FormRequest.from_response() 方法实现
            scrapy.FormRequest.from_response(response,
            meta={'cookiejar':response.meta['cookiejar']},
            dont_filter=False,
            formdata=data,
            callback=self.after_login)
            ]
    def after_login(self,response):#要爬的数据
        print('logined')
        summary = response.xpath('//*[@class="info"]/text()').extract()
        self.logger.info(summary)
