from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrape.spiders.apcd_spider import ApcdSpider  # Replace with your spider's import

process = CrawlerProcess(get_project_settings())
process.crawl(ApcdSpider)
process.start()