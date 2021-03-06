# -*- coding: utf-8 -*-
__author__ = 'HoPun'

import re

def extract_num(text):
    #从字符串中提取数字
    match_re = re.match(".*?(\d+).*",text)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums