# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Iz3ArticleItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    uuid = scrapy.Field()
    batch_id = scrapy.Field()
    spider = scrapy.Field()
    source_tag = scrapy.Field()
    source_addr = scrapy.Field()
    type = scrapy.Field()
    status = scrapy.Field()
    status_msg = scrapy.Field()
    data_uri = scrapy.Field()
    content_simhash = scrapy.Field()
    title = scrapy.Field()
    category = scrapy.Field()
    category2 = scrapy.Field()
    author = scrapy.Field()
    abstract = scrapy.Field()
    formatted_content = scrapy.Field()
    ori_content = scrapy.Field()
    formatted_text = scrapy.Field()
    imgs = scrapy.Field()
    audios = scrapy.Field()
    videos = scrapy.Field()
    content_pic = scrapy.Field()
    thumb_pic = scrapy.Field()
    audio_addr = scrapy.Field()
    video_addr = scrapy.Field()
    others = scrapy.Field()
    public_datetime = scrapy.Field()
    url_to_file_info = scrapy.Field()