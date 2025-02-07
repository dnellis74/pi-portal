import scrapy

class PageContentItem(scrapy.Item):
    source_url = scrapy.Field()
    pi_url = scrapy.Field()
    content = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    jurisdiction = scrapy.Field()
    doc_type = scrapy.Field()
    tombstone = scrapy.Field()
    language = scrapy.Field()
    mime_type = scrapy.Field()
