# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import re
import os
import sys
import logging
import json
import zipfile
import pymysql
import shutil

import scrapy
from scrapy.utils.project import get_project_settings
from scrapy.exceptions import DropItem
from iz3.libs import utils
from iz3.libs import SpiderToolkit

from scrapy.pipelines.files import FilesPipeline
import datetime
import simhash

available_keys = ['uuid', 'batch_id', 'spider', 'source_tag', 'source_addr', 'type', 'status', 'status_msg',
                  'data_uri', 'content_simhash', 'title', 'category', 'category2', 'author', 'abstract',
                  'formatted_content',
                  'ori_content', 'formatted_text', 'imgs', 'audios', 'videos', 'content_pic', 'thumb_pic',
                  'audio_addr', 'video_addr', 'others', 'public_datetime']


class Iz3Pipeline:
    def process_item(self, item, spider):
        return item


class SimHash:
    def process_item(self, item, spider):
        item['content_simhash'] = str(simhash.Simhash(item['formatted_text']))
        return item


class PackFilesPipeline:
    def __init__(self, settings):
        self.settings = settings

    def process_item(self, item, spider):
        output = self.settings['FILE_EXPORT_LOCATION']
        output_dir = os.path.join(output, "ING_" + item['data_uri'])
        output_zip_dest = os.path.join(output, "ING_" + item['data_uri'], 'raw.zip')
        final_output_dir = os.path.join(output, item['data_uri'])
        try:
            if item['status'] == 'downloaded':
                # todo: pack files into a dir and zip them
                # meta file
                meta = {}
                for key in ['uuid', 'spider', 'source_tag', 'source_addr', 'type',
                            'data_uri', 'title', 'category', 'category2', 'author', 'abstract',
                            'imgs', 'audios', 'videos', 'content_pic', 'thumb_pic',
                            'audio_addr', 'video_addr', 'others', 'public_datetime']:
                    if key in item:
                        meta[key] = item[key]
                    else:
                        meta[key] = None
                with open(os.path.join(output_dir, 'meta.json'), 'w') as f:
                    json.dump(meta, f)
                # html file
                with open(os.path.join(output_dir, 'formatted_content.html'), 'w') as f:
                    f.write(item['formatted_content'])
                # raw_html file
                with open(os.path.join(output_dir, 'ori_content.html'), 'w') as f:
                    f.write(item['ori_content'])
                # text file
                with open(os.path.join(output_dir, 'formatted_text.txt'), 'w') as f:
                    f.write(item['formatted_text'])
                # status file
                with open(os.path.join(output_dir, 'status.{}'.format(item['status'])), 'w') as f:
                    f.write("{}\n".format(item['status_msg']))
                    f.close()
                item['status'] = 'packed'

                # zip
                file_list = os.listdir(output_dir)
                with zipfile.ZipFile(output_zip_dest, 'w', zipfile.ZIP_DEFLATED) as fzip:
                    for f in file_list:
                        if f != 'raw.zip':
                            fzip.write(os.path.join(output_dir, f), f)
                # mv dir
                shutil.move(output_dir, final_output_dir)

            else:
                meta = {}
                for key in ['uuid', 'spider', 'source_tag', 'source_addr', 'type',
                            'data_uri', 'title', 'category', 'category2', 'author', 'abstract',
                            'imgs', 'audios', 'videos', 'content_pic', 'thumb_pic',
                            'audio_addr', 'video_addr', 'others', 'public_datetime']:
                    if key in item:
                        meta[key] = item[key]
                    else:
                        meta[key] = None
                with open(os.path.join(output_dir, 'meta.json'), 'w') as f:
                    json.dump(meta, f)
                # status file
                with open(os.path.join(output_dir, 'status.{}'.format(item['status'])), 'w') as f:
                    f.write("{}\n".format(item['status_msg']))
                    f.close()
        except Exception as e:
            spider.logger.error(
                "pack item[{}][{}] on[{}] error".format(item['uuid'], item['source_addr'], item['data_uri']),
                exc_info=True)
            item['status'] = 'packed_failed'
            item['status_msg'] = str(e)
        return item

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            # db_config=crawler.settings.get('DB_CONFIG')
            settings=crawler.settings
        )


class DuplicatesPipeline(object):
    def __init__(self, settings):
        self.db_config = settings.get('DB_CONFIG')
        self.conf = settings.get('DUPLICATES_PIPELINE_CONF')
        self.title_duplicated_filter_days = self.conf['DEFAULT_TITLE_DUPLICATED_FILTER_DAYS']
        self.url_duplicated_filter_days = self.conf['URL_DUPLICATED_FILTER_DAYS']
        self.spiders_should_filter_title_in_db = set(self.conf['SPIDERS_SHOULD_FILTER_TITLE_IN_DB'])
        self.conn = None
        self.seen_titles = set([])
        self.seen_urls = set([])

    def title_duplicated_filter(self, item):
        """
            检查是否title重复
        """
        if item['spider'] in self.spiders_should_filter_title_in_db and item['title'] in self.seen_titles:
            return False
        else:
            return True

    def url_duplicated_filter(self, item):
        """
            检查是否url重复
        """
        if item['source_addr'] in self.seen_urls:
            return False
        else:
            return True

    def process_item(self, item, spider):
        # filer
        if self.title_duplicated_filter(item) is False:
            raise DropItem(
                "Duplicate item(title) found: {}:{}:{}".format(item['title'], item['uuid'], item['source_addr']))
        else:
            self.seen_titles.add(item['title'])

        if self.url_duplicated_filter(item) is False:
            raise DropItem(
                "Duplicate item(url) found: {}:{}:{}".format(item['title'], item['uuid'], item['source_addr']))
            self.seen_urls.add(item['source_addr'])

        # 通过过滤
        return item

    def open_spider(self, spider):
        logging.info("=" * 20 + "DuplicatesPipeline in open_spider" + "=" * 20)
        self.conn = pymysql.connect(**self.db_config, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

        if len(self.spiders_should_filter_title_in_db) != 0:
            s_string = ", ".join(["%s"] * len(self.spiders_should_filter_title_in_db))
            sql = '''SELECT title FROM `articles` where `created_at` >= curdate() - INTERVAL %s DAY and spider in ({0})'''.format(
                s_string)
            try:
                with self.conn.cursor() as cursor:
                    cursor.execute(sql,
                                   [self.title_duplicated_filter_days] + list(self.spiders_should_filter_title_in_db))
                    ret = cursor.fetchall()
                    self.conn.commit()
                    self.seen_titles = set([rec['title'] for rec in ret])
                    spider.logger.info("init self.seen_titles({}) records from DB".format(len(self.seen_titles)))
            except Exception as e:
                spider.logger.error("init self.seen_titles records from DB error, sql[%s] exit!" % sql, exc_info=True)
                sys.exit(-1)

        sql = '''SELECT source_addr FROM `articles` where `created_at` >= curdate() - INTERVAL %s DAY'''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, [self.title_duplicated_filter_days])
                ret = cursor.fetchall()
                self.conn.commit()
                self.seen_urls = set([rec['source_addr'] for rec in ret])
                spider.logger.info("init self.seen_urls({}) records from DB".format(len(self.seen_urls)))
        except Exception as e:
            spider.logger.error("init self.seen_urls records from DB error, sql[%s] exit!" % sql, exc_info=True)
            sys.exit(-1)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            # db_config=crawler.settings.get('DB_CONFIG')
            settings=crawler.settings
        )

    def close_spider(self, spider):
        logging.info("=" * 20 + "DuplicatesPipeline in close_spider" + "=" * 20)
        self.conn.close()


class MyFilesPipeline(FilesPipeline):
    """ 下载文件完成后，检查，转储，并输出日志, 供下一步使用"""

    def open_spider(self, spider):
        logging.info("=" * 20 + "MyFilesPipeline in open_spider" + "=" * 20)
        self.spiderinfo = self.SpiderInfo(spider)
        self.proccessed = []

    def close_spider(self, spider):
        logging.info("=" * 20 + "MyFilesPipeline in close_spider" + "=" * 20)
        for item, results in self.proccessed:
            logging.info("MyFilesPipeline in close_spider download ok: %s" % item['uuid'])
        logging.info("Mission Completed in dumping reports")

    def get_media_requests(self, item, info):
        logging.info("get_media_requests: [%s]" % (item['uuid']))
        url_to_file_info = {}

        # content_images
        if not item['imgs']:
            logging.info("get_media_requests: [%s], no imgs to be download" % (item['uuid']))
        else:
            # {'id': img_id, 'url': url, 'ori_url': ori_url, 'alt': alt}
            for img in item['imgs']:
                url = img['ori_url']
                url_to_file_info[url] = ['content_image', img]
        # thumb_pic
        if not item['thumb_pic']:
            logging.info("get_media_requests: [%s], no thumb_pic to be download" % (item['uuid']))
        else:
            url = item['thumb_pic']
            img_type = SpiderToolkit.get_url_file_type(url).lower()
            url_to_file_info[url] = ['thumb_image', {'ori_url': url, 'url': "thumb_image.{}".format(img_type)}]
        # audio
        if 'audio_addr' not in item or item['audio_addr'] is None:
            logging.info("get_media_requests: [%s], no audio_addr to be download" % (item['uuid']))
        else:
            url = item['audio_addr']
            audio_type = SpiderToolkit.get_url_file_type(url).lower()
            url_to_file_info[url] = ['audio', {'ori_url': url, 'url': "audio.{}".format(audio_type)}]

        item['url_to_file_info'] = url_to_file_info
        for url in url_to_file_info:
            yield scrapy.Request(url)

    def item_completed(self, results, item, info):
        logging.info("in begin for item_completed for id:%s" % (item['uuid']))
        settings = get_project_settings()
        storage = settings['FILES_STORE']
        output = settings['FILE_EXPORT_LOCATION']
        is_error = False
        url_to_file_info = item['url_to_file_info']

        for i in range(len(results)):
            ok, result_info = results[i]
            file_url = result_info['url']
            file_type, file_info = url_to_file_info[file_url]
            if not ok:
                logging.warning("[Download File Error][%s], ignore this article[%s][%s][%s][%s]" % (
                    file_url, item['spider'], item['uuid'], item['source_addr'], result_info.getErrorMessage()))
                is_error = True
                break
            else:
                # restore it
                dest_local = os.path.join(output, "ING_" + item['data_uri'], os.path.basename(file_info['url']))
                file_downloaded_locate = os.path.join(storage, result_info['path'])
                logging.info("cp file from [%s] to [%s]" % (file_downloaded_locate, dest_local))

                if utils.mkdir_cp(file_downloaded_locate, dest_local) is False:
                    logging.error("cp file from [%s] to [%s] ERROR" % (file_downloaded_locate, dest_local))
                    is_error = True
                    break
                logging.info("PROCESS article [%s] Done" % (item['uuid']))

        if is_error is not True:
            self.proccessed.append([item, results])
            item['status'] = 'downloaded'
            item['status_msg'] = 'related files downloaded'
        else:
            item['status'] = 'downloaded_error'
            item['status_msg'] = 'related files download error'
        return item


class MysqlPipeline(object):
    """
        store items
    """

    def __init__(self, settings):
        logging.info("=" * 20 + "MysqlPipeline in open_spider" + "=" * 20)
        self.db_config = settings.get('DB_CONFIG')
        self.conn = None

    def open_spider(self, spider):
        self.conn = pymysql.connect(**self.db_config, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            # db_config=crawler.settings.get('DB_CONFIG')
            settings=crawler.settings
        )

    def process_item(self, item, spider):
        """check format and insert it into DB"""
        now = datetime.datetime.now()
        if item['status'] == 'packed':
            item['status'] = 'done'
            item['status_msg'] = 'ok'
            # available_keys = ['uuid', 'batch_id', 'spider', 'source_tag', 'source_addr', 'type', 'status', 'status_msg',
            #                   'data_uri', 'title', 'category', 'category2', 'author', 'abstract', 'formatted_content',
            #                   'ori_content', 'formatted_text', 'imgs', 'audios', 'videos', 'content_pic', 'thumb_pic',
            #                   'audio_addr', 'video_addr', 'others', 'public_datetime'
            #                   ]
            keys = [key for key in available_keys if key in item and item[key] is not None]
            full_keys = keys + ['created_at', 'updated_at']
            keys_str = ", ".join(["`%s`" % k for k in full_keys])
            s_str = ", ".join(["%s"] * len(full_keys))
            # self.logger.info("type:{}".format())
            keys_value_list = [item[k] if type(item[k]) not in (list, dict, tuple) else json.dumps(item[k]) for k in
                               keys] + [str(now), str(now)]

            sql = ("""INSERT INTO `articles` (%s) values (%s) on duplicate key """
                   """update `updated_at`=VALUES(`updated_at`)""") \
                  % (keys_str, s_str)
            try:
                with self.conn.cursor() as cursor:
                    ret = cursor.execute(sql, keys_value_list)
                    self.conn.commit()
                    spider.logger.info("dump item[%s] into DB: with ret[%s]" % (item['uuid'], ret))
            except Exception as e:
                spider.logger.error("insert item to DB error, sql[%s][%s]" % (sql, item), exc_info=True)
        else:
            # 有些异常case 不一定能落到这个阶段
            item['others']['ref_uuid'] = item['uuid']
            keys = [key for key in available_keys if key in item and item[key] is not None]
            full_keys = keys + ['created_at', 'updated_at']
            keys_str = ", ".join(["`%s`" % k for k in full_keys])
            s_str = ", ".join(["%s"] * len(full_keys))
            keys_value_list = [item[k] if type(item[k]) not in (list, dict, tuple) else json.dumps(item[k]) for k in
                               keys] + [str(now), str(now)]

            sql = ("""INSERT INTO `failed_articles` (%s) values (%s) on duplicate key update `data_uri`=`data_uri`, """
                   """`status`=VALUES(`status`), `status_msg`=VALUES(`status_msg`), `updated_at`=VALUES(`updated_at`)"""
                   """, `others`=VALUES(`others`)"""
                   ) \
                  % (keys_str, s_str)
            try:
                with self.conn.cursor() as cursor:
                    ret = cursor.execute(sql, keys_value_list)
                    self.conn.commit()
                    spider.logger.info("dump item[%s] into DB for error recording: with ret[%s]" % (item['uuid'], ret))
            except Exception as e:
                spider.logger.error("insert item to DB error, sql[%s][%s]" % (sql, item), exc_info=True)
        return item

    def close_spider(self, spider):
        logging.info("=" * 20 + "MysqlPipeline in close_spider" + "=" * 20)
        self.conn.close()
