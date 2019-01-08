# scrapy
The scrapy projects.
# 贴吧爬虫开发记录

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

> Method 1

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

> Method 2

```
def toPD(data):
    post = pd.DataFrame()
    for col in data.columns:
        coldata = []
        for value in data[col]:
            for j in value:
                coldata.append(j)
        post[col] = pd.Series(coldata)
    return post
toPD(data)

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

用scrapy 的shell调试了一下，得到了这些信息的xpath的表达式:

```
l.add_xpath('replysCount','//span[@class="threadlist_rep_num center_text"]//text()') #回复数
l.add_xpath('authorName','//span[@class="frs-author-name-wrap"]//text()') #作者名字
l.add_xpath('authorMainPageUrl','//span[@class="frs-author-name-wrap"]//@href') #作者主页链接
```
用panda处理了一下，得到如下数据:

|Index|authorMainUrl|author|posturl|replys|summary|
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
1|tieba.baidu.com/home/main/?un=%E7%BA%AF%E5%B1%|一呼吸一|tieba.baidu.com/p/5978804665|94|毛妹这个英雄是不是该削了?竞技把把都有，万金油的存在，她的盾
2|tieba.baidu.com/home/main/?un=q526246486&ie=ut|贴吧用户|tieba.baidu.com/p/5924655619|41|这波刀大家打几分
3|tieba.baidu.com/home/main/?un=%E9%99%86%E6%95%|陆散散|tieba.baidu.com/p/5984318268|3|算了 不想骂了 鱼塘水真多我佛了
4|tieba.baidu.com/home/main/?un=%E8%99%90%E7%88%|虐爆|tieba.baidu.com/p/5983683236|104|为什么你们有那么多小姐姐一起玩
5|tieba.baidu.com/home/main/?un=G7IP9&ie=utf-8&i|黎曦|tieba.baidu.com/p/5983616276|65|问几个问题

**Tips:**
- String 的startwith()方法可以接受多个参数，但必须是tuple，也就是string.startwith(('a','b'))

但此时又遇到了一个新问题，当我在pandas里进行列数据合并的时候，提示出错，应该是列长不一样，也就是某些数据有遗漏。然后用
pd.Series()解决了问题，它会将缺失的数据填充为NaN，但缺发现标题和发帖人的对应关系出错了。

这时候就抛出了一个问题，既然要保留item中数据的结构，那么在合并数据的时候，是否可以保证数据的对应关系呢？

## 2018.12.22
**新问题的新思考：**

> 目前解决问题的思路是这样的，假设一个分页有10个帖子，我一次性拿10个帖子的标题，发帖人，回复量，这10个帖子处理完了，再进行下一步。这样会遇到合并数据的问题,
其次出来的数据，也是十条一组的存储在item里面。如果我之后再想得到这个帖子的内容，回复这个帖子的人，这些人的信息，难道再去找之前的URL，再把拿到的数据去做复杂的合并吗？
这么一想觉得现在的方法不行，一开始我只是考虑到了爬这些标题做分析，但现在想要更多的数据，就必须换一种方法。

Todo:

- 有一个div有两个class，一个是gril, 另一个是hot gril, 那么在我通过girl定位到了这个“gril”之后，怎么知道她是hot girl呢？


## 新的架构

现在的方法是，利用深层爬取。刚开始的请求还是一样的，请求一页的数据，然后从中收集所有帖子的链接，这时候返回这一页的帖子链接的list，然后在一个个循环请求，回来的数据传给回调方法处理并存储到item里面。

这里的关键在于，第一页的数据抓取完了之后，得找到下一页的链接继续请求，从请求的数据中继续找帖子，找下一页，如此循环，通过指定CLOSESPIDER_ITEMCOUNT的值可以让爬虫在爬了特定的值后停下来，不然会一直继续下一页，参见下面的tips.


```
def parse(self, response):
    # get the next page info
    nextPageUrls = response.xpath("//a[@class='next pagination-item ']//@href")
    for url in nextPageUrls.extract():
        self.logger.info("=====Now request:{}=====".format(url))
        yield scrapy.Request(urljoin('https://tieba.baidu.com',url))

    # get the post urls and collec the info.
    postSubUrls = response.xpath("//a[@class='j_th_tit ']//@href").extract()
    postUrls = list(map(self.addPref,postSubUrls))
    for url in postUrls.__reversed__():
        yield scrapy.Request(url,callback=self.parsePost,meta={'url':url})

def parsePost(self,response):
    l = ItemLoader(item=TiebaItem(),response=response)
    title = response.xpath("//div[@class='core_title_wrap_bright clearfix']//text()").extract()[0]
    l.add_value("link",response.meta['url'])
    l.add_value("title",title)
    l.add_xpath("replyUsers","//div[@class='d_author']//li[@class='d_name']//a[@class='p_author_name j_user_card']//text()")
    l.add_xpath("replyContent","//div[@class='d_post_content j_d_post_content ']//text()")
    yield l.load_item()

```

上面的代码，我将下一页的请求放在抽取帖子内容后面，就会出现只能抓一页的情况，折腾了半天，后参考《精通PYTHON爬虫框架Scrapy——异步图书》代码才解决，不知何故，待研究。

一些技巧：

- [利用meta参数，在请求之间传信息](https://www.zhihu.com/question/54773510)
- 多利用 urljoin 来合并url，而不是自己写函数再map
- scrapy crawl name -s CLOSESPIDER_ITEMCOUNT=100 通过-s指定CLOSESPIDER_ITEMCOUNT的值可以让爬虫在爬了特定的值后停下来

## 2018.12.23

今天换了个个音乐主题的贴吧billboard吧抓数据，发现xpath表达式都抓不到东西了，检查了一下发现不同的吧某些东西还不一样，比如billboard吧和守望先锋吧帖子内容的class：

- “d_post_content j_d_post_content ”
- “d_post_content j_d_post_content  clearfix”

billboard吧的class增加了一个clearfix的值，这是用来清除浮动的，要了解清楚浮动是干嘛，可以参考[这篇文章](https://www.jianshu.com/p/9d6a6fc3e398)，现在有两个办法

- 找到这个clearfix的规律，有clearfix的吧或者帖子就给我们的xpath表达式加上
- 还是按照原来的方法去取值，如果取不到，那就加上clearfix

目前来看第二种方法比较简单，先试试:

```
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
l.add_xpath("replyUsers","//div[@class='d_author']//li[@class='d_name']//a[@class='p_author_name j_user_card']//text()")
# 跟帖内容
replyContent = response.xpath("//div[@class='d_post_content j_d_post_content  clearfix']//text()")
if replyContent:
    replyContent = replyContent.extract()
else:
    replyContent = response.xpath("//div[@class='d_post_content j_d_post_content ']//text()").extract()
l.add_value("replyContent",replyContent)

```
没问题，成功抓到所需要的信息,现在我要抓去更多用户的信息，这帖子回复的人是个妹子还是汉子那肯定得知道不，通过分析html结果，被我发现了这么一个字段:

```
data-field="{

    "author":{"user_id":2350893056,"user_name":"GYGGYFDDH","name_u":"GYGGYFDDH&ie=utf-8","user_sex":2,"portrait":"00c84759474759464444481f8c","is_like":1,"level_id":6,"level_name":"\u51cc\u6ce2\u55b5\u6b65","cur_score":118,"bawu":0,"props":null,"user_nickname":"\u767d\u00ba\u82d7\u7f2a"},

    "content":{"post_id":123353095371,"is_anonym":false,"open_id":"tbclient","open_type":"android","date":"2018-12-23 10:35","vote_crypt":"","post_no":1,"type":"0","comment_num":0,"is_fold":0,"ptype":"0","is_saveface":false,"props":null,"post_index":0,"pb_tpoint":null}
    
    }"
```

这就是突破口了，author是用户的信息，content是这个帖子的信息，比如回复的时间。user_sex就是性别，1是男，2是女，仔细一看这里面还有用户的设备信息，比如用的是苹果还是安卓。
试着抓一些信息下来，xpath表达式如下：

```

l.add_xpath("replyUsers","//div[@class='p_postlist']/div/attribute::data-field")

```

选取所有class是p_postlist的第一个子节点，然后选择它的叫做data-field的属性，即上面的信息了，抓到了所有的数据，用pd过滤一下：

```
usernames = []
usersexs = []
for users in sxyData.replyUsers:
    for userinfo in users:
        userInfoString = "".join(userinfo)
        if userInfoString.startswith("{"):
            user = pd.read_json(userInfoString)
            usernames.append(user.author["user_name"])
            usersexs.append(user.author["user_sex"])
users = {'names':usernames,'sex':usersexs}
users = pd.DataFrame(users)
users
```

这里会从中提取出用户名和性别，因为某些数据不是以{}包装的，所以在用pd提取json对象之前，先判断一下,得到的数据如下：
```
0	夜和海1996	1
1	华丽atobekeigo	2
5	永中一小生	0
6	哦啦啦旅途啦	0
7	lzlzyz	1

```
- 1：男生
- 2：女生
- 0:未知

## todo

- 下午突然想到，应该可以通过子或父节点获取这个class的属性，再去提取信息，这样就不需要判断了，直接可以根据相对关系选择它的class名

## 2018.12.24
在处理抓帖子内容的时候出现一些问题，因为有一些帖子的评论很多，也是有下一页的，虽然处理逻辑和帖子列表的差不多，但仔细研究后发现是不一样的，并且找出了之前的代码的缺陷:

```
def parse(self, response):
        # get the post urls and collec the info.
        postSubUrls = response.xpath("//a[@class='j_th_tit ']//@href").extract()
        self.logger.info("==============Now Request pages==========={}".format(postSubUrls))
        for subrul in postSubUrls:
            url = urljoin(self.urlPrefix,subrul)
            self.logger.info("----------Now request url============={}".format(url))
            yield scrapy.Request(url,callback=self.parsePost,meta={'url':url})

        # get the next page info
        nextPageUrls = response.xpath("//a[@class='next pagination-item ']//@href")    
        for url in nextPageUrls.extract():
            yield scrapy.Request(urljoin(self.urlPrefix,url),callback=self.parse)

```

主要是这里的抓帖子内容和下一页的顺序对调了，以及之前我在yield下一页的时候，竟然没有指定回掉方法，这导致第一页帖子里面就有些帖子没有抓下来。随后开始研究如何抓第二页的评论，此处遇到一个大坑, 即第二页的标题变了，变成了"回复： {原来的标题}",导致新抓下来的标题都
存到了另一个字段，我还以为没抓下来，一直在改，之所以存到了下一个字段，是因为我在下一页的请求发起之前，就已经yield返回了l.load_item().

找到原因了就好办了，对于那些抓下一页的评论的帖子，它的title我们可以一开始就指定，然后通过meta传递给下一个请求，在下一个请求中判断如果meta中有title，那么title就设置为meta中的，这里在判断meta(meta是一个字典)中是否某个key的时候犯了个小错,我是这么写的:

```
if d.meta['apples']:
```

但其实应该这样写:

```
if 'apples' in d:
```
参见：[Check key exist in python dict](https://stackoverflow.com/questions/44035287/check-key-exist-in-python-dict/44035382)

但这样抓下来的帖子还是有一个问题，当爬虫爬下一个评论页的时候，这一页的数据它就会返回，所以在json数据中，就会有标题，链接重复，但评论和跟帖用户不一样的数据，本来的数据是一个帖子一条数据，但现在是只要这个帖子又下一页的评论，就会新建一条数据，虽然它的标题和链接是一样的。

## 2018.12.26
这问题困扰了我好几天，还是没有找到解决的办法，尝试过:

- 在爬取comments的过程中，不yeild数据，将爬下来的评论append给meta，回调方法指向自身，重复直到没有下一页为止，但这样scrapy直接把之前的数据都丢掉了，可能是因为每次重新
进入方法的时候，都new了一个新的itemLoader。

> 暂时搁置一下，反正帖子标题是一样的，后面用pandas处理一下吧。

我想提取出来的数据是，每个comments作为一条记录，同时记录帖子的标题和用户，但比对抓下来的数据后发现评论中的用户数量和评论本身不一致，这就尴尬了，不建立好对应关系，数据根本就没办法分析啊。

不过基本可以确定，评论中的第一条就是楼主，先把楼主的信息抓出来吧。

## 2019.01.07

今天了解到scrapy的另一个特性，即CrawlSpider类型的爬虫，在这个爬虫里面，它可以像下面这样去抽取post的连接和下一页的链接：

```
rules = (
    Rule(LinkExtractor(restrict_xpaths="//div[@class='pb_footer']//ul[@class='l_posts_num']//a"),callback='parse'),
    Rule(LinkExtractor(restrict_xpaths="//a[@class='j_th_tit ']"),callback='parsePost')
)

```

《精通python爬虫》这本书上说：

> Rule中可以指定回调函数，也就是上面我写的callback='parse'(这里只能是函数的字符串名字，而不是self.parse)。如果我们没有指定callback函数，那么scrapy将会跟踪已经抽取的链接，如果你希望跟踪链接，那么需要再callback中使用return或yield返回它们，或者将Rule的follow参数设置为true，当你的页面既包含item又包含其他有用的导航链接时，该功能可能会非常有用。

看完这一段，我有几个疑问：

- callback函数中，如何拿到想跟踪的链接？
- yield的链接，直接返回这个链接，还是返回response对象？
- 返回的数据（或者链接），由谁来处理？


rules: 是Rule对象的集合，用于匹配目标网站并排除干扰
parse_start_url: 用于爬取起始响应，必须要返回Item，Request中的一个。

查了一些资料，rules的规则：

```
rules = [
    Rule(
        link_extractor,     # LinkExtractor对象
        callback=None,      # 请求到响应数据时的回调函数
        cb_kwargs=None,     # 调用函数设置的参数,不要指定为parse
        follow=None,        # 是否从response跟进链接，为布尔值
        process_links=None, # 过滤linkextractor列表，每次获取列表时都会调用
        process_request=None    # 过滤request,每次提取request都会调用
    )
] 

```

LinkExtractor的参数
```

class scrapy.contrib.linkextractor.sgml.SgmlLinkExtractor(
    allow = (),         # 符合正则表达式参数的数据会被提取
    deny = (),          # 符合正则表达式参数的数据禁止提取
    allow_domains = (),     # 包含的域名中可以提取数据
    deny_domains = (),      # 包含的域名中禁止提取数据
    deny_extensions = (),       
    restrict_xpath = (),        # 使用xpath提取数据，和allow共同起作用
    tags = (),          # 根据标签名称提取数据
    attrs = (),         # 根据标签属性提取数据
    canonicalize = (),
    unique = True,          # 剔除重复链接请求
    process_value = None
)

```

# xpath参考
```
1. 进入scrapy调试界面
scrapy shell 'url'

2. 调试界面使用xpath
response.xpath('')

3. 抓取指定类的元素,//为获取所有元素，返回的是list，所有如果在上一级使用了//,那么下一级也是用//,如果是/,那么提取的就是该list中的第一个元素
xpath('//div[@class="title"]//text()'),text()为获取该元素下的文本，如果需要纯文本，还需要在后面加extract()方法

4. 提取属性
xpath("//div[@class='pb_footer']//ul[@class='l_posts_num']//a//@href"),主要是后面的@href


```

# scrapy参考
## setting
> 这里说的设置，只要在setting.py中添加一条记录即可

1. 设置utf-8格式，避免中文出错
FEED_EXPORT_ENCODING = 'utf-8'

2. 不遵守网站的爬虫策略
ROBOTSTXT_OBEY = False

## commands
1. 启动爬虫
scrapy crawl CrawlerName

2. 启动爬虫，导出数据为json
scrapy crawl CrawlerName -o filename.json 

3. 爬了指定的数据后，就关闭
scrapy crawl CrawlerName -o filename.json -s CLOSESPIDER_ITEMCOUNT=50

# Linux 连接 Windows SMB共享文件夹

1. 安装pysmb, pip install pysmb
2. 导入相关的包
3. 使用方法见注释

> 参考：
- [SMBConnection Class](https://pysmb.readthedocs.io/en/latest/api/smb_SMBConnection.html)
- [一个小任务](http://melonteam.com/posts/cong_yi_ge_xiao_ren_wu_kai_shi__python_xue_xi_bi_ji/#%E5%85%B3%E4%BA%8E%E7%88%AC%E8%99%AB)

```
from smb.SMBConnection import SMBConnection
# 新建连接对象
conn = SMBConnection('domain_user_name', 'you_password', 'device_hostname', 'server_ip', domain = 'domain_address', use_ntlm_v2=True, is_direct_tcp=True)
# 返回值为布尔型，表示连接成功与否
result = conn.connect('server_ip', 445)

# 检索文件
for f in conn.listPath('share_folder_name','folder_name_in_prvious_one'):
    print(f.filename)
```
