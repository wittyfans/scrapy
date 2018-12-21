# scrapy
The scrapy projects.
# 
## 抓取数据并存储
因为我要抓取很多链接，最开始的想法就是直接把所有的url给内置的start_urls方法，于是我自己写了个生成器，直接怼给了它，但发现不管用。
翻了下官方的文档：
> make_requests_from_url() 将被调用来创建Request对象。 该方法仅仅会被Scrapy调用一次，因此您可以将其实现为生成器

于是就自己写了生成器给make_requests_from_url() 用，在把response 返回:

```
def start_requests(self):
    self.logger.info("START:")
    for url in self.getBBSUrl("守望先锋",10):
        yield self.make_requests_from_url(url)
```
> 但后面又发现这个在最新的官方文档里面没有, 原来, Spider.make_requests_from_url is deprecated (issue 1728, fixes issue 1495), 看来又要改一下才行，先挖个坑吧。

*更新：*

看了下官方的例子:

```
Return multiple Requests and items from a single callback:

import scrapy

class MySpider(scrapy.Spider):
    name = 'example.com'
    allowed_domains = ['example.com']
    start_urls = [
        'http://www.example.com/1.html',
        'http://www.example.com/2.html',
        'http://www.example.com/3.html',
    ]

    def parse(self, response):
        for h3 in response.xpath('//h3').extract():
            yield {"title": h3}

        for url in response.xpath('//a/@href').extract():
            yield scrapy.Request(url, callback=self.parse)

```
直接将 yield self.make_requests_from_url(url) 换成 yield scrapy.Request(url, callback=self.parse) 就好了。

之前是使用直接赋值的方式来将xpath解析到的值给item，也就是:

```
def parse(self, response):
    alltitles = []
    item = TiebaItem()
    titles = response.xpath("//a[@class='j_th_tit ']//text()").extract()
    for title in titles:
        alltitles.append(title)
    item["summarys"] = alltitles
    return item
```

titles是一个页面中所有的title，是一个数组对象，但发现如果我直接将title赋值到item，也是可以的，这里纯粹多此一举，所以变成:

```
def parse(self, response):
    item = TiebaItem()
    titles = response.xpath("//a[@class='j_th_tit ']//text()").extract()
    item["summarys"] = titles
    return item
```

后面改用了ItemLoader，ItemLoader是更抽象的一种使用方式。我们知道，数据都是存储在item里面的，每次使用的时候都需要创建item，之后再
通过response.xpath选择需要的值，赋值给item里面对应的字段。

itemLoader把这个过程抽象为，你在新建itemLoader的时候把要装数据的item给我，然后只需要给我字段和要存的值就好，另一个好处是，你还可以在itemLoader这个环节对一些数据做处理，比如首尾空格去除，添加特定字段等。

所以修改后的存储代码变成了这样:

```
def parse(self, response):
        l = ItemLoader(item=TiebaItem(),response=response)
        l.add_xpath("summarys","//a[@class='j_th_tit ']//text()")
        l.add_xpath("links",'//a[@class="j_th_tit "]//@href')
        return l.load_item()

```
另一种方式:

```
def parse(self, response):
    post = l.nested_xpath("//a[@class='j_th_tit ']")
    post.add_xpath('summary', 'text()')
    post.add_xpath('link', '@href')
    return l.load_item()

```


现在我提取了帖子的两条数据，一个是标题，另一个是标题的链接，存储在item里面是这个样子的：
```
[
    {"summarys":["标题1","标题2"],"Links":["Link1","Link2"]},
    {"summarys":["标题3","标题4"],"Links":["Link3","Link4"]}
]

```

这基本上是请求一次，返回了贴吧里面一页的数据，然后从中提取了所有标题和链接，所以是一次请求，一行数据。那有没有办法把所有的标题和链接合并到一起呢？也就是从多个请求提取到的数据存到item中的同一个字段里。

仔细想想这样有必要吗？用pd分析一下这个json数据看看。

```
summarys = []
links = []

for link in data.link:
    for value in link:
        url = "tieba.baidu.com"+str(value)
        links.append(url)
for summary in data.summary:
    for value in summary:
        summarys.append(value)
post = pd.DataFrame()
post["summarys"] = summarys
post["link"] = links
post

```

输出的数据：

```
0	哈哈哈哈大幺蛾子	tieba.baidu.com/p/5982395208
1	安娜玩家表示看到堡垒和奥丽莎就高兴，打不动靶太安逸了	tieba.baidu.com/p/5984392212
2	这个200hz的有人用过吗，和144的差多少?平常只打守望先	tieba.baidu.com/p/5978507290
3	这麦克雷是挂吗 大家帮忙看看	tieba.baidu.com/p/5984115608
4	我真是服了，削猪的时候，我不出声，因为我不玩；削76的时候，	tieba.baidu.com/p/5982819128
5	这难道就是开窍了吗？	tieba.baidu.com/p/5979734484

```

检查了下链接，跟标题一样，那就先这样吧，继续研究深度爬取，多抓一些信息。

