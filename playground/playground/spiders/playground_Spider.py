import scrapy
from playground.items import PlaygroundItem
import json
# start_requests() 读取 start_urls 中的URL， 并以 parse 为回调函数生成 Request

class playground_Spider(scrapy.Spider):
    name = "playground"
    allowed_domains = ["servicedesk.homecredit.cn","baidu.com"]
    # start_urls = [
    #     "https://servicedesk.homecredit.cn/login.jsp"
    # ]

# os_destination: 
# user_role: 
# atl_token: 
# login: Log+In
    def start_requests(self):
        return [scrapy.FormRequest("https://servicedesk.homecredit.cn/login.jsp",formdata = {
            'os_username': 'fan.zhangfz',
            'os_password': '13579qwerASDF'
                }, callback = self.logged_in
            )
        ]

    def logged_in(self, response):
       yield scrapy.Request("https://servicedesk.homecredit.cn/rest/servicedesk/1/servicedesk/IN/issuelist?jql=project+%3D+%22IN%22+AND+status+in+(Open%2C+%22In+Progress%22%2C+Reopened%2C+Waiting%2C+%22Processing+In+Change+Management%22)+AND+Location+%3D+Changsha+AND+%22Assigned+Group%22+%3D+%22Helpdesk+CN%22&columnNames=issuekey&columnNames=project&columnNames=issuetype&columnNames=priority&columnNames=reporter&columnNames=customfield_10208&columnNames=customfield_10202&columnNames=summary&columnNames=status&columnNames=assignee&columnNames=created&columnNames=updated&columnNames=customfield_10121&columnNames=customfield_10120&columnNames=issuelinks&columnNames=subtasks&issuesPerPage=50",callback=self.parseChs)
    def parseChs(self,response):
        item = PlaygroundItem()
        # summarys = response.xpath('//*[@class="summary"]//text()').extract()
        js = json.loads(response.body)

        item['summary'] = js
        return item

        
"""
上面logged_ine是一个回调函数，处理返回的数据，处理完成之后，需要
返回一个数据，这个数据可以是：
1. items里面定义好的对象
2. request
3. 可迭代的容器
"""

"""
1. 如果是多个网址，需要用一个生成器去返回网址，当然这个生成器也可以直接写在start_requests里面，
直接用生成器返回request对象
2. start_requets方法需要返回一个request对象，这个对象接受url，可以定义callback函数来处理抓回来
的request数据, using scrapy.Request(url,callback=)
"""