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

现在我提取了帖子的两条数据，一个是标题，另一个是标题的链接，存储在item里面是这个样子的：
```
[
    {"summarys":["标题1","标题2"],"Links":["Link1","Link2"]},
    {"summarys":["标题3","标题4"],"Links":["Link3","Link4"]}
]

```

这基本上是请求一次，返回了贴吧里面一页的数据，然后从中提取了所有标题和链接，所以是一次请求，一行数据。那有没有办法把所有的标题和链接合并到一起呢？也就是从多个请求提取到的数据存到item中的同一个字段里。

