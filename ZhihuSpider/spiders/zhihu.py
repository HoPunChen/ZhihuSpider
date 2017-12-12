# -*- coding: utf-8 -*-
import scrapy
import re
import json
import time
import requests
try:
    import urlparse as parse
except:
    from urllib import parse

try:
    from PIL import Image
except:
    pass

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

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
        response_text = response.text
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url,url) for url in all_urls]
        all_urls = filter(lambda x:True if x.startswith("https") else False,all_urls)

        for url in all_urls:
            print(url)
            match_obj = re.match("(.*zhihu.com/question/(/d+))(/|$).*",url)
            if match_obj:
                request_url = match_obj.group(1)
                request_id = match_obj.group(2)
                print(request_id,request_url)
            pass

    def parse_detail(self,response):
        pass

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

            im = Image.open('captcha.jpg')
            im.show()
            im.close()

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
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter = True, headers = self.header)








