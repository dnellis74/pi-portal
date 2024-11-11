import scrapy

class PageContentItem(scrapy.Item):
    url = scrapy.Field()
    content = scrapy.Field()
    key = scrapy.Field()
