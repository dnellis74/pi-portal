import csv
import os
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse
import logging
import random  # For random delay
from datetime import datetime  # For timestamped logs
import json # for dumping dicts
from bs4 import BeautifulSoup


class ApcdOnBaseSpider(CrawlSpider):
    name = "apcd_onbase"
    allowed_domains=['cdphe.colorado.gov',
                     'urldefense.proofpoint.com']
    start_urls=     ["https://cdphe.colorado.gov/apcd"]
    rules = (
        Rule(LinkExtractor(), callback='parse_item', follow=True),
    )
    # Optimized settings for better performance
    custom_settings = {
        'DOWNLOAD_DELAY': random.uniform(0.1, .5),  # Random delay between requests to reduce rate-limiting
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,  # Lower retries to avoid wasting time on persistent failures
        'RETRY_HTTP_CODES': [429, 500, 502, 503, 504],  # Retry on these HTTP errors
        'CONCURRENT_REQUESTS': 64,  # Adjust concurrency to balance speed and reliability
        'REDIRECT_ENABLED': True,
        'REDIRECT_MAX_TIMES': 10,
        'DOWNLOAD_TIMEOUT': 120,  # Increase timeout slightly for slower responses
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',  # Use a common user-agent
        'COOKIES_ENABLED': False,  # Disable cookies to avoid tracking
        'ROBOTSTXT_OBEY': False,  # Ignore robots.txt for comprehensive scraping
        'LOG_LEVEL': 'INFO',  # Log level
        'LOG_STDOUT': True,  # Log to stdout (terminal)
        'DEPTH_LIMIT': 5,
    }    

    def __init__(self, *args, **kwargs):
        super(ApcdOnBaseSpider, self).__init__(*args, **kwargs)
        self.download_dir = 'download/onbase_links'
        # self.reset_download_folder()
        os.makedirs(self.download_dir, exist_ok=True)
        self.file = open(self.download_dir + '/onbase_link.csv', 'a')
        self.csvWriter = csv.writer(self.file)
        
    def __exit__(self, exc_type, exc_value, traceback):
        # Close the file when exiting the 'with' block
        self.file.close()

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all anchor tags
        anchor_tags = soup.find_all('a')
        
        # Iterate over each anchor tag and extract attributes and content
        for tag in anchor_tags:
            href = tag.get('href')  # Extract the href attribute
            content = tag.text      # Extract the content inside the tag
            # Check if the link belongs to the allowed domain
            if href and 'hylandcloud' in href:
                url = response.url
                title = soup.title.string
                # Print the link if it belongs to the allowed domain
                self.logger.info(f'{title}{content},{href},{url}')
                self.csvWriter.writerow([title, content, href, url])                
        return

    def handle_error(self, failure):
        # Log all errors and handle retries with exponential backoff
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}", level=logging.ERROR)
