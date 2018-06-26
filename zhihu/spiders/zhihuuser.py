import json

from scrapy import Spider,Request

from zhihu.items import UserItem


class ZhihuuserSpider(Spider):
    name = 'zhihuuser'
    # 重写了start_requests，这两个变量不会被调用
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    # **************************************************
    start_user = 'he-jia-43'
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'

    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    # 只在开始时执行一次，3个yield都被执行
    def start_requests(self):
        # 创建解析'he-jia-43'用户信息的请求
        yield Request(self.user_url.format(user=self.start_user,include=self.user_query),self.parse_user)
        # 创建解析'he-jia-43'关注人的第一页请求
        yield Request(self.follows_url.format(user=self.start_user,include=self.follows_query,offset=0,limit=20),callback=self.parse_follows)
        # 创建解析'he-jia-43'粉丝的第一页请求
        yield Request(self.followers_url.format(user=self.start_user,include=self.follows_query,offset=0,limit=20),callback=self.parse_followers)




    # 每调用一次函数三个yield都被执行一次
    def parse_user(self, response):
        result = json.loads(response.text)
        item = UserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        # 保存解析到的个人各项信息
        yield item
        # 创建解析当前对象的关注人请求
        yield Request(self.follows_url.format(user=result.get('url_token'),include=self.follows_query,limit=20,offset=0),self.parse_follows)
        # 创建解析当前对象的粉丝请求
        yield Request(self.followers_url.format(user=result.get('url_token'),include=self.follows_query,limit=20,offset=0),self.parse_followers)


    def parse_follows(self, response):
        results = json.loads(response.text)
        if 'data' in results.keys():
            # 20个data代表20个关注人
            for result in results.get('data'):
                # 循环执行yield
                # 将当前页的所有关注人发送到个人信息的请求
                yield Request(self.user_url.format(user=result.get('url_token'),include=self.user_query),self.parse_user)
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
           # 执行yield一次
            # 扫描完当前页，执行下一页的请求
            yield Request(next_page,self.parse_follows)


    def parse_followers(self, response):
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                # 循环执行yield
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              self.parse_user)
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            # 执行yield一次
            yield Request(next_page, self.parse_followers)
