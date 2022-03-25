"""
    spider for voa learning english
"""
import datetime

import scrapy
from .OurBaseSpider import OurBaseSpider
from iz3.libs import utils, SpiderToolkit
from urllib.parse import urljoin, urlparse
from iz3.items import Iz3ArticleItem
import bs4
from bs4 import BeautifulSoup as SOUP
import re
import string


class LevoaSpider(OurBaseSpider):
    name = 'levoa'
    # allowed_domains = ['learningenglish.voanews.com']
    allowed_domains = []
    # 写爬虫的时候voa好像有些bug
    start_urls = ['https://learningenglish.voanews.com/z/952?p=0']
    # start_urls = ['https://learningenglish.voanews.com/z/1579?p=1']

    # start_urls = ['http://www.baidu.com']
    max_page_counter = 100
    mp3_text_re = re.compile(r'(?i)(\d+) kbps')

    def parse(self, response):
        """
            parse
        :param response:
        :return:
        """
        # self.logger.debug("parsing url: " + response.url)
        # self.logger.debug("ori content:" + response.text)
        page_counter = response.meta.get('page_counter', 0)

        list_page_type = LevoaSpider.check_list_page_type(response)
        if list_page_type == 'common':
            divs = response.xpath('//ul[@id="articleItems"]/li/div[contains(@class, "media-block")]')
        else:  ### async
            divs = response.xpath('//li/div[contains(@class, "media-block")]')
        # check entries
        should_break = False
        for div in divs:
            entry_info = self.extract_entry_info(div)
            if entry_info['entry_uri'] is None:
                self.logger.error("entry_uri should not be None, please check url:[{}]".format(response.url))
                continue
            elif entry_info['ignore'] is True:
                if entry_info['entry_uri'] is None:
                    self.logger.info("entry_uri should be ignore, please check url:[{}]".format(response.url))
                else:
                    self.logger.info("entry_uri should be ignore, please check url:[{}][{}]".format(
                        response.url, entry_info['entry_uri']))
                continue

            entry_info['entry_url'] = urljoin(response.url, entry_info['entry_uri'])
            del entry_info['entry_uri']
            # check pubtime
            formatted_public_datetime_str = entry_info['formatted_public_datetime_str']
            pubtime = datetime.datetime.strptime(formatted_public_datetime_str, "%Y-%m-%d %H:%M:%S")
            if pubtime < self.endtime:
                self.logger.info("{} < {} for url:{}, break".format(pubtime, self.endtime, entry_info['entry_url']))
                should_break = True
                break

            request = scrapy.Request(entry_info['entry_url'], callback=self.parse_item_contents,
                                     headers={'Referer': response.url}, meta={'entry_info': entry_info})
            yield request

        if len(divs) == 0 or should_break is True or page_counter >= self.max_page_counter:
            pass
        else:
            page_counter += 1
            parsed_url = urlparse(response.url)
            next_page_url = parsed_url._replace(query='p={}'.format(page_counter)).geturl()
            self.logger.info("NEXT PAGE: {}:{}".format(page_counter, next_page_url))
            request = scrapy.Request(next_page_url, callback=self.parse,
                                     headers={'Referer': self.start_urls[0]}, meta={'page_counter': page_counter})
            yield request

    def extract_entry_info(self, div):
        # 缩略图
        thumb_pic_url = div.xpath('.//div[contains(@class, "thumb")]/img/@data-src').extract_first()
        if thumb_pic_url is None:
            thumb_pic_url = div.xpath('.//div[contains(@class, "thumb")]/img/@src').extract_first()
        # public date
        public_date_str = div.xpath(
            './/div[contains(@class, "media-block__content")]/span[contains(@class, "date")]/text()').extract_first()
        formatted_public_datetime_str = utils.news_date_format(public_date_str)
        entry_uri = div.xpath('a/@href').extract_first()

        # todo 加入 meadia type 检查 有个 xx flex 标记
        ignore = False
        if div.xpath('.//span[contains(@class, "ico--media-type")]').extract_first() is not None:
            ignore = True

        return {'thumb_pic_url': thumb_pic_url, 'formatted_public_datetime_str': formatted_public_datetime_str,
                'entry_uri': entry_uri, 'ignore': ignore}

    @staticmethod
    def check_list_page_type(response):
        if len(response.xpath('//ul[@id="articleItems"]')) != 0:
            return 'common'
        elif len(response.xpath('//li/div[contains(@class, "media-block")]')) != 0:
            return 'async'
        else:
            return 'error'

    def parse_item_contents(self, response):
        self.logger.info("parse_item_contents: {}".format(response.meta))
        item = Iz3ArticleItem()

        soup = SOUP(response.body, 'lxml')

        # common
        item['uuid'] = SpiderToolkit.uuid1()
        item['spider'] = self.name
        item['source_tag'] = self.name
        item['status'] = 'new'
        item['status_msg'] = 'new'
        item['thumb_pic'] = response.meta['entry_info']['thumb_pic_url']
        item['source_addr'] = response.url
        item['batch_id'] = self.batch_id
        item['data_uri'] = "{}/{}".format(str(item['batch_id'])[:6], item['uuid'])

        layout_type = self.get_levoa_layout_type(response, soup)
        status = False
        if layout_type == 'common':
            item, status = self.extract_common(response, soup, item)
        if 'audio_addr' in item and item['audio_addr'] is not None and item['audio_addr'] != '':
            item['type'] = 'w_audio'
        else:
            item['type'] = 'wo_audio'

        if status is True and self.check_item_status(item):
            yield item

    def check_item_status(self, item):
        return True

    def extract_common(self, response, soup, item):
        ok = True
        content_soup = soup.find('div', id='content')
        header_soup = content_soup.find('div', class_='hdr-container')
        body_soup = content_soup.find('div', class_='body-container')
        header_xpath = response.xpath('//div[contains(@class, "hdr-container")]')
        body_xpath = response.xpath('//div[contains(@class, "body-container")]')
        others = {}
        others['tags'] = ['voa', 'voa learning english']

        # title
        title = header_xpath.xpath(
            '//div[contains(@class, "col-title")]/h1[contains(@class, "title")]/text()').extract_first('').strip()
        item['title'] = title

        # public_datetime
        public_datetime = header_xpath.xpath('//div[contains(@class, "published")]/span/time/@datetime').extract_first(
            '').strip()
        if public_datetime == '':
            header_xpath.xpath('//div[contains(@class, "published")]/span/time/text()').extract_first('').strip()
        if public_datetime != '':
            item['public_datetime'] = utils.news_date_format(public_datetime)
        else:
            item['public_datetime'] = utils.news_date_format(self.now)

        # content_pic
        content_pic_xpath = header_xpath.xpath(
            '//div[contains(@class, "cover-media")]/figure[contains(@class, "media-image")]//img')
        content_pic_url = content_pic_xpath.xpath('@src').extract_first('').strip()
        content_pic_alt = content_pic_xpath.xpath('@alt').extract_first('').strip()
        item['content_pic'] = content_pic_url
        others['content_pic'] = {'url': 'content_pic.', 'ori_url': content_pic_url, 'alt': content_pic_alt}

        # category
        category = header_xpath.xpath(
            '//div[contains(@class, "col-category")]/div[contains(@class, "category")]/a/text()').extract_first(
            '').strip()
        if category != '':
            others['tags'].append(category)
        item['category'] = category

        # audio
        audio_a_xpaths = body_xpath.xpath(('//div[contains(@class, "media-pholder--audio")]/' \
                                           'div[@class="media-download"]//div[@class="inner"]//li[@class="subitem"]/a'))
        audio_a_texts = audio_a_xpaths.xpath("text()").extract()
        if len(audio_a_xpaths) != 0:
            min_i = 0
            min_value = 1024
            for i, atext in enumerate(audio_a_texts):
                m = self.mp3_text_re.search(atext)
                if m is not None:
                    i_kbps = int(m.group(1))
                    if i_kbps < min_value:
                        min_value = i_kbps
                        min_i = i
            audio_a_xpath = audio_a_xpaths[min_i]
            audio_addr = audio_a_xpath.xpath('@href').extract_first()
            item['audio_addr'] = audio_addr
            item['audios'] = []
            item['audios'].append({'type': 'main', 'addr': audio_addr})
        else:
            item['audios'] = None

        article_content_soup = body_soup.find('div', id='article-content')
        if article_content_soup is None:
            ok = False
            return item, ok

        ori_content, formatted_content, formatted_text, footers, \
        img_infos, video_infos = self.extract_content(response, article_content_soup)
        others['footer'] = str(footers)
        item['ori_content'] = ori_content
        item['formatted_content'] = formatted_content
        item['formatted_text'] = formatted_text

        # imgs
        item['imgs'] = img_infos

        # others
        item['others'] = others

        return item, ok

    def get_levoa_layout_type(self, response, soup):
        return 'common'

    def extract_content(self, response, article_content_soup):
        ori_content_soup = article_content_soup.find('div', class_='wsw')
        ori_content = str(ori_content_soup)
        formatted_content_soup, footers, img_infos, video_infos = self.clean_content(response, ori_content_soup)
        lines = [line.strip() for line in formatted_content_soup.text.split("\n") if len(line.strip()) != 0]
        formatted_text = "\n".join(lines)

        return ori_content, str(formatted_content_soup), formatted_text, footers, img_infos, video_infos

    def clean_content(self, response, ori_content_soup):
        # for every children
        children = list(ori_content_soup.children)
        in_footer_flag = False
        footers = []
        img_counter = 1
        img_infos = []
        video_infos = []

        for i, child in enumerate(children):
            # empty string?
            if type(child) == bs4.element.NavigableString:
                if not str(child).strip() == '':
                    self.logger.warning(
                        "invalid NavigableString found:[{}], delete it anyway, check {}".format(child.strip(),
                                                                                                response.url))
                child.extract()
                continue
            elif child.name == 'div':  # classify
                try:
                    div_type = self.classify_div(child)
                except Exception as e:
                    self.logger.error("div:{} url:{}".format(child, response.url))
                if div_type in ('main_audio', 'clear', 'content_video', 'unknown'):
                    child.decompose()
                elif div_type == 'content_image':
                    new_div_soup, img_info = self.extract_img_div(child, img_counter)
                    img_infos.append(img_info)
                    img_counter += 1
                    child.replace_with(new_div_soup)
                else:
                    child.decompose()
                continue
            elif child.name == 'p':  # classify
                p_text = child.text.strip()
                p_text_set = list(set(p_text))

                if len(p_text_set) != 0 and p_text_set[0] == '_' and len(p_text) > 10:
                    child.decompose()

                elif p_text.lower() in ('words in this story',):
                    in_footer_flag = True

                if in_footer_flag is True:
                    footers.append(child.extract())

            elif child.name in ('h2',):
                c_text = child.text.strip()
                if c_text.lower() in ('words in this story',):
                    in_footer_flag = True

                if in_footer_flag is True:
                    footers.append(child.extract())
            else:
                continue

        new_children = list(ori_content_soup.children)

        last_size = 20
        last_children = new_children[-1 * last_size:]
        last_size = len(last_children)
        ending_p_index = None
        for j in range(last_size - 1, -1, -1):
            j_child = last_children[j]
            if j_child.name == 'p':
                j_child_text = j_child.text.strip().lower()
                j_child_words = [w.strip(string.punctuation) for w in j_child_text.split()]
                if len(j_child_words) >= 2 and len(j_child_words) <= 5:
                    if j_child_text.startswith("i'm") or j_child_text.startswith("i am") or j_child_text.startswith(
                            'i’m'):
                        # this is the ending p
                        ending_p_index = j
                        break
        # forward
        if ending_p_index is not None:
            for j in range(ending_p_index, last_size):
                j_child = last_children[j]
                if j_child.text.strip() == '':
                    j_child.decompose()
                if len(j_child.find_all('em')) != 0:
                    j_child_text = j_child.text.strip()
                    j_child_em_text = "".join([em.text for em in j_child.find_all('em')]).strip()
                    if j_child_text == j_child_em_text:
                        j_child.decompose()
        return ori_content_soup, footers, img_infos, video_infos

    @staticmethod
    def extract_img_div(div, id_counter):
        img = div.find('div', class_='thumb').find('img')
        ori_url = img['src'].strip()
        img_type = SpiderToolkit.get_url_file_type(ori_url).lower()
        if img_type not in ('png', 'jpg', 'jpeg', 'bmp', 'webp'):
            img_type = 'unknown'
        alt = img['alt'].strip()
        div_id = 'content_image_div_{}'.format(id_counter)
        img_id = 'content_image_{}'.format(id_counter)
        url = "{}.{}".format(img_id, img_type)
        image_div_html = SpiderToolkit.gen_formatted_img_html(div_id, img_id, url, alt, alt, ori_url)
        return SOUP(image_div_html, 'html.parser'), {'id': img_id, 'url': url, 'ori_url': ori_url, 'alt': alt}

    @staticmethod
    def classify_div(div):
        if div.find('div', class_='media-pholder') is not None:
            return 'main_audio'
        elif div.find('div', class_='quiz') is not None:
            return 'quiz'
        elif 'class' in div and div['class'] == 'clear':
            return 'empty'
        elif div.find('div', class_='external-content-placeholder') is not None:
            return 'content_video'
        elif div.find('iframe') is not None:
            iframe = div.find('iframe')
            if 'youtube' in str(iframe.find('script')):
                return 'content_video'
        elif div.find('figure', class_='media-image') is not None:
            return 'content_image'
        else:
            return 'unknown'
