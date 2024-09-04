from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrape.spiders.apcd_onbase_spider import ApcdOnBaseSpider  # Replace with your spider's import

process = CrawlerProcess(get_project_settings())
process.crawl(ApcdOnBaseSpider)
process.start()