# -*- coding: utf-8 -*-
__author__ = 'HoPun'

import requests
try:
    #python2
    import http.cookielib
except:
    #python3
    import http.cookiejar as cookielib

import re

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename = "cookies.txt")
try:
    session.cookies.load(ignore_discard = True)
except:
    print("cookie未能加载")

agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"
header = {
    "HOST":"www.zhihu.com",
    "Referer":"https://www.zhihu.com/",
    "User-Agent":agent
}

def get_xsrf():
    #获取xsrf code
    response = session.get("https://www.zhihu.com",headers = header)
    match_obj = re.match('.*name="_xsrf" value="(.*)"',response.text)
    if match_obj:
       return match_obj.group(1)
    else:
        return ""

def get_index():
    response = session.get("https://www.zhihu.com", headers = header)
    with open("index_page.html","wb") as f:
        f.write(response.text.encode("utf-8"))
    print("ok")

def zhihu_login(account,password):
    #知乎登录
    if re.match("(1[34578][0-9]{9})",account):
        print("手机号码登录")
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            "_xsrf":get_xsrf(),
            "phone_num":account,
            "password":password
        }

        response_text = session.post(post_url,data = post_data,headers = header)
        session.cookies.save()

get_index()