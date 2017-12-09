# -*- coding: utf-8 -*-
import scrapy
import re
import json
import time
import requests


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
        all_urls = response.css("a::attr(href)").extract()
        pass

    def start_requests(self):
        return [scrapy.Request("https://www.zhihu.com/#signin",headers = self.header,callback = self.longin)]

    def longin(self,response):
        if self.is_login:
            print('您已经登录')
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.header)
        else:
            account = input('请输入你的用户名\n>  ')
            password = input("请输入你的密码\n>  ")
            response_text = response.text
            match_obj = re.match('.*name="_xsrf" value="(.*?)"', response_text,re.DOTALL)
            xsrf = ""
            if match_obj:
                xsrf = match_obj.group(1)
                if xsrf:
                    post_url = "https://www.zhihu.com/login/phone_num"
                    post_data = {
                        "_xsrf": xsrf,
                        "phone_num": account,
                        "password": password
                    }
                    response_text = self.session.post(url = post_url, data=post_data, headers= self.header)
                    text_json = response_text.json()
                    if text_json['r'] == 1:
                        # 不输入验证码登录失败
                        # 使用需要输入验证码的方式登录
                        post_data["captcha"] = self.get_captcha()

                        return [scrapy.FormRequest(
                            url = post_url,
                            formdata = post_data,
                            headers = self.header,
                            callback = self.check_login,
                        )]

    def get_captcha(self):
        t = str(int(time.time() * 1000))
        captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
        r = self.session.get(captcha_url, headers = self.header)
        with open('captcha.jpg', 'wb') as f:
            f.write(r.content)
            f.close()
            # 用pillow 的 Image 显示验证码
            # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入

            im = Image.open('captcha.jpg')
            im.show()
            im.close()

        captcha = input("please input the captcha\n>")
        return captcha

    def check_login(self,response):
        # 验证服务器的返回数据判断是否成功
        text_json = json.loads(response.text)
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter = True, headers = self.header)

    def is_login(self):
        # 通过个人中心页面返回状态码来判断是否为登录状态
        inbox_url = "https://www.zhihu.com/inbox"
        response = self.session.get(inbox_url, headers=self.header, allow_redirects=False)
        if response.status_code == 200:
            return True
        else:
            return False




