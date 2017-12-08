# -*- coding: utf-8 -*-
__author__ = 'HoPun'

import requests
try:
    #python2
    import http.cookielib
except:
    #python3
    import http.cookiejar as cookielib

import time
import re

try:
    from PIL import Image
except:
    pass

session = requests.session()
#使读取和保存文件更容易
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

def is_login():
    #通过个人中心页面返回状态码来判断是否为登录状态
    inbox_url = "https://www.zhihu.com/inbox"
    response = session.get(inbox_url,headers = header,allow_redirects = False)
    if response.status_code == 200:
        return True
    else:
        return False
    pass

def get_xsrf():
    #获取xsrf code
    response = session.get("https://www.zhihu.com",headers = header)
    match_obj = re.match('.*name="_xsrf" value="(.*?)"',response.text)
    if match_obj:
       return match_obj.group(1)
    else:
        return ""

# 获取验证码
def get_captcha():
    t = str(int(time.time() * 1000))
    captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
    r = session.get(captcha_url, headers = header)
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
    else:
        if "@" in account:
            print("邮箱登录")
        else:
            print("你的账号输入有问题，请重新登录")
        post_url = "https://www.zhihu.com/login/email"
        post_data = {
            "_xsrf": get_xsrf(),
            "email": account,
            "password": password
        }

    response_text = session.post(post_url, data = post_data, headers=header)
    login_code = response_text.json()
    if login_code['r'] == 1:
        # 不输入验证码登录失败
        # 使用需要输入验证码的方式登录
        post_data["captcha"] = get_captcha()
        response_text = session.post(post_url, data = post_data, headers = header)
        login_code = response_text.json()
        # 保存 cookies 到文件，
        #  下次可以使用 cookie 直接登录，不需要输入账号和密码
        # print(login_code['msg'])
    session.cookies.save()


if __name__ == '__main__':
    if is_login():
        print('您已经登录')
    else:
        account = input('请输入你的用户名\n>  ')
        password = input("请输入你的密码\n>  ")
        zhihu_login(account,password)