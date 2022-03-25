# Scrapy settings for iz3 project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import logging
import os

BOT_NAME = 'iz3'
CONF_ENV = 'dev'

SPIDER_MODULES = ['iz3.spiders']
NEWSPIDER_MODULE = 'iz3.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'iz3 (+http://www.yourdomain.com)'
# USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36"

USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS = 4

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'iz3.middlewares.Iz3SpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'iz3.middlewares.Iz3DownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # 'iz3.pipelines.Iz3Pipeline': 300,
    # 1.url任务去重, title等去重
    'iz3.pipelines.DuplicatesPipeline': 301,
    # 2.下载文件
    'iz3.pipelines.MyFilesPipeline': 305,
    # 3.质检
    #'iz3.pipelines.MyGuardPipeline': 308,
    # 3. 打包
    'iz3.pipelines.PackFilesPipeline': 310,
    # 4.入库
    'iz3.pipelines.MysqlPipeline': 360,
    # 5.记录batch信息
    # 'iz3.pipelines.BatchPipeline': 366
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

_CUR_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = _CUR_DIR

### project  confs ###
LOG_ENABLED = False
###
LOG_DIR = os.path.join("logs")
# LOG_DIR = "/tmp/scrapy/logs" # for dev
LOG_FORMAT_STR = '%(asctime)s [%(name)s][%(levelname)s][%(filename)s:%(lineno)s]: %(message)s'
# DEBUG < INFO < WARNING < ERROR < CRITICAL
LOG_LEVEL = logging.INFO
# 'S' : Seconds, 'M' : Minutes, 'H' : Hours, 'D' : Days, 'W' : Week day
LOG_ROTATE_UNIT = 'MIDNIGHT'
# How many log files for on log we reserved
LOG_BACKUP_COUNT = 30
# shall we print it into stdout?
LOG_STDOUT = True
LOG_FORMATTER='iz3.libs.PoliteLogFormatter'

# DB 配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345678',
    'database': 'iz3_scrapy'
}

FILE_EXPORT_LOCATION = os.path.join(BASE_DIR, 'output/')

# 这个字段会被用来拼凑未来下图片的保存地址, 会被写入数据库
# 后续处理的机器会处理位于此处的图片(这个不是爬虫机器的路径)
# IMG_DIR = 'imgs/'
# IMG_DIR = '/home/zixun/img/'

# IMG_DIR = os.path.join(BASE_DIR, 'tmp', 'storages', 'images')

# 下载文件的临时存储路径
FILES_STORE = os.path.join(BASE_DIR, 'tmp', 'storages')

# 往前看多久
BACK_HOURS = {
    'default': 24 * 1
}

# BASE_DIR = '/home/work/ZiXun/ZiXun/'
# FILE_EXPORT_LOCATION = os.path.join(BASE_DIR, 'output/')
# IMG_DIR = '/home/zixun/img/'
# BACK_HOURS = 48

# TITLE_DUPLICATED_FILTER
# 用TITLE去重的时候，加载多少天内的TITLE？
TITLE_DUPLICATED_FILTER_DAYS = 300
# URL 去重支持的加入
URL_DUPLICATED_FILTER_DAYS = 300

# CUSTOM_URL_DIR = '/tmp/urls'
MEDIA_ALLOW_REDIRECTS = True
REDIRECT_ENABLED = True


# 会将图片文件cp到这个地方
# IMG_PATCH_CP_SUB = ['/home/zixun','/home/stuser/remotehost/zixundata/picprocessindata'] # online, on test
# IMG_PATCH_CP_SUB = ['/home/zixun','/tmp/taotie/remote/'] #on dev

DUPLICATES_PIPELINE_CONF ={
    "DEFAULT_TITLE_DUPLICATED_FILTER_DAYS": 300,
    "URL_DUPLICATED_FILTER_DAYS": 300,
    "SPIDERS_SHOULD_FILTER_TITLE_IN_DB": ['levoa', ],
}

