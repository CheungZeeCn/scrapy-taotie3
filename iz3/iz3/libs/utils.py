#!/usr/bin/env python
# -*- coding: utf-8 -*-
# by zhangzhi @2016-12-05 19:13:14
# Copyright 2016 NONE rights reserved.
"""
File descriptions in one line

more informations if needed
"""

import datetime
import re
import os
import shutil
import logging


def hello(name="world"):
    """ Say Hello
    Function Descriptions here in multiple lines.
    Function Descriptions here in multiple lines.
    Args:
        name: your name, default to be world
    Returns:
        explain what will be returned here.
    Raises:
        IOERrror: What exceptions may be raised, and when
    """
    print("Hello,", name)

def main():
    """ Just Main It """
    hello()

def date_format(time_string):
    """
    function: format item[date]
    by zhongp 2016-11-29

    Tips：
    Input time_string should be formated to string like "%Y-%m-%d" or "%Y-%m-%d %H:%M" or "%Y-%m-%d %H:%M:%S"
    or current time will be returned.
    """
    now = datetime.datetime.now()
    nowdatestr = now.strftime("%Y-%m-%d")
    nowdate = datetime.datetime.strptime(nowdatestr, "%Y-%m-%d")
    nowtimestr = now.strftime("%H:%M:%S")

    if re.match(r"\d\d\d\d-\d+-\d+ \d+:\d+:\d+$", time_string):
        pass
    elif re.match(r"\d\d\d\d-\d+-\d+ \d+:\d+$", time_string):
        time_string = time_string + ":00"
    elif re.match(r"\d\d\d\d-\d+-\d+$", time_string):
        ts = datetime.datetime.strptime(time_string[0:10], "%Y-%m-%d")
        if nowdate > ts:
            time_string = ts.strftime("%Y-%m-%d") + " 23:59:00"
        else:
            time_string = ts.strftime("%Y-%m-%d") + " " + nowtimestr
    elif re.match(r'\d{4}年\d{2}月\d{2}日 \d{2}:\d{2}$', time_string):
        # added by zhangz@2017-01-23 for match pattern like: 2017年01月03日 08:19
        ts = datetime.datetime.strptime(time_string, "%Y年%m月%d日 %H:%M")
        time_string = ts.strftime("%Y-%m-%d %H:%M:00")
    elif re.match(r'\d{2}-\d{2} \d{2}:\d{2}$', time_string):
        # added by zhangz@2016-12-09 for match pattern like: 12-06 17:54
        time_string = "%04s" % now.year + "-" + time_string + ":00"
    elif re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\+|-)\d{2}:\d{2}$', time_string):
        ts = datetime.datetime.fromisoformat(time_string)
        time_string = ts.strftime("%Y-%m-%d %H:%M:%S")
    elif re.match(r'(?i)(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}$', time_string):
        ts = datetime.datetime.strptime(time_string, "%B %d, %Y")
        time_string = ts.strftime("%Y-%m-%d %H:%M:%S")
    elif re.match(r'(?i)(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}, \d{4}$', time_string):
        ts = datetime.datetime.strptime(time_string, "%b %d, %Y")
        time_string = ts.strftime("%Y-%m-%d %H:%M:%S")
    else:
        time_string = nowdatestr + " " + nowtimestr

    return time_string

def news_date_format(time_string):
    """
        call date_format, 
        and calc the right time of a news_date
        rely on zp's date_format.    

        WHY? time_string have to be early than NOW 
    """
    format_str = date_format(time_string)
    ## ensure it is a legal datetime
    now_datetime = datetime.datetime.now() 
    format_datetime = datetime.datetime.strptime(format_str, "%Y-%m-%d %H:%M:%S")
    if format_datetime > now_datetime:
        format_str = datetime.datetime.strftime(format_datetime, "%04d" % (format_datetime.year-1) + "-%m-%d %H:%M:%S")
    return format_str  


def make_dir_there(dir_name):
    ret = True
    if not os.path.exists(dir_name):
        try:
            # create directory (recursively)
            os.makedirs(dir_name)
        except OSError as e:
            logging.error("Create Dir[%s] ERROR [%s]" % (
                           dir_name, e))
            ret = False
    return ret


def mkdir_cp(from_location, to_location):
    ok = True                                                                                                                      
    try:                                                                                                                           
        dest_dir = os.path.dirname(to_location)                                                                                    
        if dest_dir != '':
            ok = make_dir_there(dest_dir)
        shutil.copy(from_location, to_location)                                                                                    
    except Exception as e:                                                                                                         
        logging.error("cp file error!![%s] to [%s] [%s]" % (from_location, to_location, e))                                        
        ok = False                                                                                                                 
    return ok


if __name__ == '__main__':
    main()

