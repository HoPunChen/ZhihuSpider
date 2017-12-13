# -*- coding: utf-8 -*-
import scrapy
import re
import json
import time
import requests
import datetime
try:
    import urlparse as parse
except:
    from urllib import parse

try:
    from PIL import Image
except:
    pass

from scrapy.loader import ItemLoader
from ZhihuSpider.items import ZhihuQuestionItem,ZhihuAnswerItem

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    # question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"

    agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"
    header = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com/",
        "User-Agent": agent
    }
    session = requests.session()

    def parse(self, response):
        """
        提取出html页面中的所有url,并跟踪这些url进行进一步爬取
        如果提取的url中格式为 /question/xxx  就下载之后直接进入解析函数
        """
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url,url) for url in all_urls]
        # all_urls = filter(lambda x:True if x.startswith("https") else False,all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*",url)
            if match_obj:
                #如果提取到question相关页面则下载后交由提取函数提取
                request_url = match_obj.group(1)
                yield scrapy.Request(url = request_url,headers = self.header,callback = self.parse_question)
            else:
                #如果不是question页面则进一步跟踪
                yield scrapy.Request(url,headers = self.header,callback = self.parse)


    def parse_question(self,response):
        #处理question页面，从页面中提取出具体的question item
        match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
        question_id = match_obj.group(2)

        item_loader = ItemLoader(item = ZhihuQuestionItem(),response = response)
        item_loader.add_css("title","h1.QuestionHeader-title::text")
        item_loader.add_css("content",".QuestionHeader-detail")
        item_loader.add_value("url",response.url)
        item_loader.add_value("zhihu_id",question_id)
        item_loader.add_css("answer_num",".List-headerText span::text")
        item_loader.add_css("comments_num",".QuestionHeader-Comment button::text")
        item_loader.add_css("watch_user_num",".NumberBoard-value::text")
        item_loader.add_css("topics",".QuestionHeader-topics .Popover div::text")

        question_item = item_loader.load_item()
        yield scrapy.Request(self.start_answer_url.format(question_id,20,0),headers = self.header,callback = self.parse_answer)
        yield question_item

    def parse_answer(self,response):
        #处理question的answer
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        #提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url,headers = self.header, callback = self.parse_answer)




    def start_requests(self):
        t = str(int(time.time() * 1000))
        captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + '&type=login&lang=en'
        return [scrapy.Request(url = captcha_url,headers = self.header,callback = self.get_captcha)]

    def login(self,response):
            response_text = response.text
            match_obj = re.match('.*name="_xsrf" value="(.*?)"', response_text,re.DOTALL)
            xsrf = ""
            if match_obj:
                xsrf = match_obj.group(1)
                if xsrf:
                    post_url = "https://www.zhihu.com/login/phone_num"
                    post_data = {
                        "_xsrf": xsrf,
                        "phone_num": "your phone number",
                        "password": "your password",
                        "captcha": response.meta['captcha']
                    }

                    return [scrapy.FormRequest(
                        url = post_url,
                        formdata = post_data,
                        headers = self.header,
                        callback = self.check_login,
                    )]

    def get_captcha(self,response):
        print(response.meta.get("post_data"))
        with open('captcha.jpg', 'wb') as f:
            f.write(response.body)
            f.close()
            # 用pillow 的 Image 显示验证码
            # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入

            # im = Image.open('captcha.jpg')
            # im.show()
            # im.close()

        captcha = input("please input the captcha\n>")
        return scrapy.FormRequest(
            url ='https://www.zhihu.com/#signin',
            headers = self.header,
            callback = self.login,
            meta = {'captcha': captcha}
        )

    def check_login(self,response):
        # 验证服务器的返回数据判断是否成功
        text_json = json.loads(response.text)
        print(text_json["msg"])
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter = True, headers = self.header)








