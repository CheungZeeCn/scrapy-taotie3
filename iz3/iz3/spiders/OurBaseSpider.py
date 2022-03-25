# -*- coding: utf-8 -*-
"""
    init
        cheungzeecn@gmail.com @20210321
"""

import os
import sys
import time
import logging
import logging.handlers
import datetime
import scrapy
import hashlib


class OurBaseSpider(scrapy.Spider):
    """ A Base Class for Us
    通过继承我们的OurBaseSpider, 规范日志的打印和输出
    """
    #incase ...
    name = "OurBaseSpider"
    total = 0
    now = datetime.datetime.now()
    batch_id = None
    today = None
    endtime = None

    def __init__(self, *args, **kwargs):
        super(OurBaseSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        raise NotImplementedError

    def get_picpath(self):
        return os.path.join(self.settings['IMG_DIR'], self.now.strftime('%Y%m%d'),
            self.name, self.now.strftime('%H%M%S'))

    def get_endtime(self):
        key = self.settings['BACK_HOURS'].get(self.name, 'default')
        back_hours = self.settings['BACK_HOURS'][key] if self.settings['BACK_HOURS'][key] else 1
        return self.now - datetime.timedelta(hours=int(back_hours))

    def get_endtime_ts(self):
        key = self.settings['BACK_HOURS'].get(self.name, 'default')
        back_hours = self.settings['BACK_HOURS'][key] if self.settings['BACK_HOURS'][key] else 1
        return time.time() - int(back_hours) * 3600

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        print("IN OurBaseSpider::from_crawler!!!!")
        spider = cls(*args, **kwargs)
        spider._set_crawler(crawler)
        spider._setup_loggers()
        spider.batch_id = int(spider.now.strftime("%Y%m%d%H%M%S"))
        spider.today = spider.now.strftime("%Y-%m-%d 00:00:00")
        spider.endtime = spider.get_endtime()
        return spider

    def incr_total(self):
        """简易计数器，临时方案，不可重入, 每次+1后返回counter值"""  
        self.total += 1
        return self.total

    '''
    def gen_article_id(self):
        total = self.incr_total()
        id_str = self.now.strftime('%Y%m%d%H%M%S%f') + "_" + self.name + "_" + str(total)
        return id_str
    '''

    def gen_article_id(self, url="", title=""):
        total = self.incr_total()
        if url == '':
            id_str = self.now.strftime('%Y%m%d%H%M%S%f') + "_" + self.name + "_" + str(total)
        else:
            if self.name in self.settings['SPIDERS_SHOULD_FILTER_TITLE_IN_DB']:
                if type(title) == unicode:
                    title = title.encode('utf-8')
                hash_str = title
            else:
                if type(url) == unicode:
                    url = url.encode('utf-8')
                hash_str = url

            obj = hashlib.md5()
            obj.update(hash_str)
            digest = obj.hexdigest()
            id_str = "0" + "_" + self.name + "_" + digest
        return id_str



    def custom_format_content_filter_after(self, text, key):
        return text

    def custom_format_content_filter_before(self, soup, key):
        return soup   

    def _setup_loggers(self):
        """
            logs setup
            1. We get log paths in our settings(dir log for default)
            2. check and create log dir
            3. set logger file names
            4. rotate logfile by a specific period

            After setup:
                root logger:  logging.info(log_message)
                scrapy logger:  Please leave it with scrapy
                spider logger: self.logger.info(log_message)

            At this very moment, we store all the output into the the same file:
                self.name+".log"  or  self.name+".wf.log"
        """
        # print("Existing settings: %s" % self.settings['LOG_DIR'])

        # dir and files
        log_dir = self.settings['LOG_DIR'] if self.settings['LOG_DIR'] else 'logs'
        log_file_name = os.path.join(log_dir, "%s.log" % (self.name))
        log_file_name_wf = os.path.join(log_dir, "%s.wf.log" % (self.name))
        if not os.path.exists(log_dir):
            try:
                # create directory (recursively)
                os.makedirs(log_dir)
            except OSError as e:
                logging.error("Spider[%s] init Failed Create Log Dir[%s] ERROR [%s]" % (
                    self.name, log_dir, e))
                sys.exit(-1)

        # format
        format_str = self.settings['LOG_FORMAT_STR'] if (
            self.settings['LOG_FORMAT_STR']) else (
                '%(asctime)s [%(name)s][%(levelname)s]'
                '[%(filename)s:%(lineno)s]: %(message)s')
        # formatter
        formatter = logging.Formatter(format_str)

        # logger instances
        root_logger = logging.getLogger()
        scrapy_logger = logging.getLogger('scrapy')
        spider_logger = logging.getLogger(self.name)

        # log level
        log_level = self.settings['LOG_LEVEL'] if (
            self.settings['LOG_LEVEL']) else logging.DEBUG

        # how to rotate
        log_rotate_unit = self.settings['LOG_ROTATE_UNIT'] if (
            self.settings['LOG_ROTATE_UNIT']) else 'D'

        #log stdout
        log_stdout = self.settings['LOG_STDOUT'] if self.settings['LOG_STDOUT'] else True

        #log backup count
        log_backup_count = self.settings['LOG_BACKUP_COUNT'] if (
            self.settings['LOG_BACKUP_COUNT']) else 30

        # finally, Handlers
        #  ROTATE !
        #   for  all
        log_handler = logging.handlers.TimedRotatingFileHandler(
            log_file_name, when=log_rotate_unit,
            backupCount=log_backup_count)
        log_handler.setLevel(log_level)
        log_handler.setFormatter(formatter)
        #split them for future usage
        root_logger.addHandler(log_handler)
        spider_logger.addHandler(log_handler)
        scrapy_logger.addHandler(log_handler)

        #   for >= WARNING
        log_handler = logging.handlers.TimedRotatingFileHandler(
            log_file_name_wf, when=log_rotate_unit,
            backupCount=log_backup_count)
        log_handler.setLevel(logging.WARNING)
        log_handler.setFormatter(formatter)

        #split them for future usage
        root_logger.addHandler(log_handler)
        spider_logger.addHandler(log_handler)
        scrapy_logger.addHandler(log_handler)

        if log_stdout:
            log_handler = logging.StreamHandler()
            log_handler.setLevel(log_level)
            log_handler.setFormatter(formatter)

            root_logger.addHandler(log_handler)
            spider_logger.addHandler(log_handler)
        # do not propagate
        spider_logger.propagate = False
