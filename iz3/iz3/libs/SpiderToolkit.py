#!/usr/bin/env python
# -*- coding: utf-8 -*-
# by zhangzhi @2017-09-18 17:29:44
# Copyright 2017 NONE rights reserved.
"""
爬虫页面处理的工具箱
"""
import re
import logging
import os
import uuid
import urllib

__author__ = 'cheungzeecn@gmail.com'
__version__ = '0.1'




'''
def clean_illegal_content_list_empty(ucontent_list):
    """ 
		处理爬虫抓取的正文内容列表，将其中的非ta字符去掉
        arguments:
        ucontent_list -- unicode 编码的内容列表, 列表
    """
    ret = []
    for uline in ucontent_list:
        ret.append(clean_line_emoji(clean_illegal_line_empty(uline)))
    return ret

def clean_illegal_line_empty(uline):
    uline_cleaned = re.sub(
            ur"\t|\n|\u3000|&nbsp;|\xa0|&#x3000;|\r|\u00a0",
            '',
            uline.strip())
    return uline_cleaned

def clean_line_emoji(uline):
    emoji_pattern = re.compile(u"[^\U00000000-\U0000d7ff\U0000e000-\U0000ffff]", flags=re.UNICODE)
    uline_cleaned = emoji_pattern.sub(r'', uline.strip())
    return uline_cleaned

def empty_strip(utext):
    return re.sub(ur"^(\r|\n|\s|\u200b|\u3000)+|(\r|\n|\s|\u200b|\u3000)+$", '', utext)

def img_url_filter(urls):
	"""
		过滤地址非法的图片, 当前版本仅仅取http和ftp开头的图片,只要是要取出base64的图片
        arguments:
		urls -- 图片的地址列表
	"""
	filtered_urls = [i.strip() for i in urls if \
   		i.strip().startswith('http') or i.strip().startswith('ftp')]	
	return filtered_urls

def gen_pic_path_pair(local_base, item_id, imgs_url):
	pic_path = []
	img_picpath = {}
	for i in range(len(imgs_url)):
	    temp = os.path.join(local_base, '{0}_{1}.jpg'.format(item_id, i))
	    pic_path.append(temp)
	    img_picpath[imgs_url[i]] = temp

	return pic_path, img_picpath

def strQ2B(ustring):
    """unicode 把字符串全角转半角 针对数字和英文"""
    rstring = u""
    utarget = u"０１２３４５６７８９ｑｗｅｒｔｙｕｉｏｐａｓｄｆｇｈｊｋｌｚｘｃｖｂｎｍ－ＱＷＥＲＴＹＵＩＯＰＡＳＤＦＧＨＪＫＬＺＸＣＶＢＮＭ"
    for uchar in ustring:
        if uchar not in utarget:
            rstring += uchar
            continue
        inside_code=ord(uchar)
        if inside_code==0x3000:
            inside_code=0x0020
        else:
            inside_code-=0xfee0
        if inside_code<0x0020 or inside_code>0x7e:   #转完之后不是半角字符返回原来的字符
            rstring += uchar
        rstring += unichr(inside_code)
    return rstring

def unify_html_br(ustring): 
    return re.sub(ur"(<br */>)+", '<br />', ustring)

def format_content_by_reserve_styles(spider, soup, main_content, img_picpath, key="default"):
    """ 接收Unicode的content, 直接提取URL
                                                          zhangz@2017-01-22
        todo:
            这块有一个耦合, 业务使用了 SOGOU_WEIXIN_IMG_BLACK_LIST_ADDR 配置，非微信爬虫使用也不影响，
            考虑到时间和工作量，所以暂时就先不去把逻辑放出来了。 

        当前这个函数适用的爬虫:
        sogou-wx-gzh-plus
    """
    formcon = []
    img_in_soup = []

    # 去掉链接
    for a_tag in main_content.find_all("a"):
        #a_tag.decompose()
        # inorder to decompose(), I replace it with ti's text
        # @zhangz
        a_tag.replaceWith(a_tag.text)

    # 去视频
    for iframe_tag in main_content.find_all("iframe"): 
        iframe_tag.decompose()   

    # 去语音
    for audio_tag in main_content.find_all("mpvoice"): 
        audio_tag.decompose()
    for audio_tag in main_content.find_all("qqmusic"): 
        audio_tag.decompose()
    for audio_tag in main_content.find_all("span", class_=["db", "audio_area"]): 
        audio_tag.decompose()
    for audio_tag in main_content.find_all("span", class_=["tc", "tips_global", "unsupport_tips"]): 
        audio_tag.decompose()

    ## 拆开span ? 先注释掉
    #for span_tag in main_content.find_all("span"):
    #    span_tag.unwrap()

    # 去广告
    for blockquote_tag in main_content.find_all("blockquote"):
        blockquote_tag.decompose()

    for ad_tag in main_content.find_all("div", {"id": "js_sponsor_ad_area"}):
        ad_tag.decompose()

    # rm script
    for script_tag in main_content.find_all("script"):
        script_tag.decompose()
    
    # img 转 本地 img 地址
    img_content = main_content.find_all("img")
    if img_content and len(img_picpath):
        for uimg in img_content:
            del uimg['alt']
            # keep base 64 the same 
            # by zhangz
            # only http and ftp file we will download later
            uimg_src =  ''
            uimg_src_ori =  ''
            if uimg.has_attr('src') and (uimg['src'].strip().startswith('http') or uimg['src'].strip().startswith('ftp')):
                if uimg['src'].strip() in img_picpath:
                    uimg_src = img_picpath[uimg['src'].strip()]
                    uimg_src_ori = uimg['src']
            elif uimg.has_attr('data-src') and (uimg['data-src'].strip().startswith('http') or uimg['data-src'].strip().startswith('ftp')):
                if uimg['data-src'].strip() in img_picpath:
                    uimg_src = img_picpath[uimg['data-src'].strip()]
                    uimg_src_ori = uimg['data-src']
            else:
                spider.logger.warning("failed in getting src from img tag, plz check key[%s], uimg[%s]" % (key, uimg))
                continue

            should_decompose = False
            for blocked_url in spider.settings['SOGOU_WEIXIN_IMG_BLACK_LIST_ADDR']:
                #spider.logger.warning("###"* 30 + blocked_url)
                #spider.logger.warning("###"* 30 + uimg_src_ori)
                if blocked_url in uimg_src_ori:
                    #spider.logger.warning("###"* 30 + "IN")
                    # 去掉黑名单内的图片
                    should_decompose = True
                    break 
                else:
                    pass

            if should_decompose == True:
                uimg.decompose()
                continue
            else:
                # modify style
                if uimg.has_attr('style') and 'height' in uimg['style']:
                    uimg['style'] = re.sub(r'height:\s*\d+px', 'height:auto', uimg['style'])                   
                uimg['src'] = uimg_src
                img_in_soup.append(uimg['src'])
                spider.logger.debug("uimg:%s" % (uimg['src']))


    #spider.logger.debug("="*100)
    #spider.logger.debug(main_content)
    #spider.logger.debug("="*100)

    ## section 保留样式
    #for sec in main_content.find_all("section"):
    #    sec.unwrap()

    # p cleaning 
    for p in main_content.find_all("p"):
        if p.text.strip() == '' and p.find('img') == None: # 这个 P 没有存在意义
            spider.logger.debug("decompose P: %s" % p)
            p.decompose() 
            continue
        if p.string != None:
            ustr = p.string.strip()
            ustr = re.sub(ur'^(<br */>)+', '', ustr)
            ustr = re.sub(ur' <', '<', ustr)
            ustr = re.sub(ur' <', '<', ustr)
            ustr = re.sub(ur'> ', '>', ustr)
            ustr = re.sub(ur"\t|\n|\u3000|&nbsp;|\xa0|&#x3000;|\r", '', ustr)
            if ustr == '':
                p.decompose()    
            continue

        # 保留 P
        #br_tag = soup.new_tag("br")
        #p.insert_after(br_tag)
        #p.unwrap()

    format_content = unicode(main_content).strip()
    format_content = format_content.replace("\n", "")
    format_content = re.sub(ur'^(<br */>)+', '', format_content.strip())
    format_content = re.sub(ur'\s+<', '<', format_content)
    format_content = re.sub(ur'>\s+', '>', format_content)
    #format_content = re.sub(ur'<p.*?>', '', format_content)
    #format_content = re.sub(ur'</p>', '<br/>', format_content)
    format_content = re.sub(ur"\t|\n|\u3000|&nbsp;|\xa0|&#x3000;|\r", '', format_content)
    return format_content 


def format_content_by_split_p(spider, soup, main_content, img_picpath, key="default"):
    """ 接收Unicode的content, 就是正文内容， 做个性化的处理后，返回格式化的内容
        有时候图片不在p里面就会丢失或者错位，做了一个hack，给图片包了一层p标签, 从而防止图片丢失
                                                          zhangz@2017-01-22

        当前这个函数适用的爬虫:
        JrjSpider
    """
    formcon = []
    img_in_soup = []

    imgs = main_content.find_all("img")
    for img in imgs:
        img.wrap(soup.new_tag("p"))

    tables = main_content.find_all("table")
    for table in tables:
        # ignore this article
        return ''
        table.wrap(soup.new_tag("p"))

    save_content = main_content.find_all("p")

    # 先广遍历 
    for each in save_content:
        # 去掉 p， 由于做了hack, 有可能出现p包含p的情况
        for p_tag in each.find_all("p"):
            p_tag.unwrap()
        # 去掉 a
        for a_tag in each.find_all("a"):
            #a_tag.decompose()
            # inorder to decompose(), I replace it with ti's text
            # @zhangz
            # a_tag.replaceWith(a_tag.text)
            # a better choice
            a_tag.unwrap()
        # strong 转 b
        for strong_tag in each.find_all("strong"):
            strong_tag.name = "b"
        # 去视频
        for iframe_tag in each.find_all("iframe"): 
            iframe_tag.decompose()   

        # img 转 本地 img 地址
        img_content = each.find_all("img")
        if img_content and len(img_picpath):
            for uimg in img_content:
                del uimg['alt']
                # keep base 64 the same 
                # by zhangz
                # only http and ftp file we will download later
                if uimg.has_attr('src') and (uimg['src'].strip().startswith('http') or uimg['src'].strip().startswith('ftp')):
                    if uimg['src'].strip() in img_picpath:
                        uimg['src'] = img_picpath[uimg['src'].strip()]
                        img_in_soup.append(uimg['src'])
                elif uimg.has_attr('data-src') and (uimg['data-src'].strip().startswith('http') or uimg['data-src'].strip().startswith('ftp')):
                    if uimg['data-src'].strip() in img_picpath:
                        uimg['src'] = img_picpath[uimg['data-src'].strip()]
                        img_in_soup.append(uimg['src'])
                        spider.logger.debug("uimg:%s" % (uimg['src']))
                else:
                    spider.logger.warning("failed in getting src from img tag, plz check key[%s], uimg[%s]" % (key, uimg))

        ustr = unicode(each)
        ustr = re.sub(ur'^(<br */>)+', '', ustr.strip())
        ustr = re.sub(ur' <', '<', ustr)
        ustr = re.sub(ur'> ', '>', ustr)
        ustr = re.sub(ur'<p.*?>', '', ustr)
        ustr = re.sub(ur'</p>', '<br/>', ustr)
        ustr = re.sub(ur"\t|\n|\u3000|&nbsp;|\xa0|&#x3000;|\r", '', ustr)
        if re.sub(ur'(<br */>)+', '', ustr) == '':
            formcon.append('')
        else:
            formcon.append(ustr)

    format_content = ''.join(formcon)

    return format_content

'''


def uuid1():
    return str(uuid.uuid1())

def gen_formatted_img_html(div_id, img_id, url, alt, caption, ori_url):
    tmpl = """<div id="{0}" class="iz3ContentImage">
    <img id="{1}" alt="{3}" class="iz3ContentImage" src="{2}" ori_src="{5}">
    <span class="iz3ContentImageCaption">
    {4}
    </span>
    </div>"""
    html = tmpl.format(div_id, img_id, url, alt, caption, ori_url)
    return html

def get_url_file_type(url):
    return os.path.basename(urllib.parse.urlparse(url).path).split('.')[-1]

def main():
    print("hello")


	
if __name__ == '__main__':
    main()

