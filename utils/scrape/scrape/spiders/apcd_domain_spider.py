import csv
import os
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
import logging
import random

class APcdLinkSpider(CrawlSpider):
    name = "apcd_domains"
    # Use absolute path to the JSON file
    json_path = r"C:\Users\loren\OneDrive\Documents\Python Scripts\pi-portal\pi-portal\public\apcd_domains.json"

    # Load allowed domains and allowed URLs from the JSON file
    with open(json_path, 'r') as f:
        config = json.load(f)

    # Ensure the keys are in the JSON
    allowed_domains = config.get("allowed_domains", [])
    allowed_urls = config.get("allowed_urls", [])
    allowed_domains = allowed_domains  # Load allowed domains from JSON
    start_urls = ["https://cdphe.colorado.gov/apcd"]  # Start at the parent domain

    # Rule to only follow links that match the allowed URLs
    rules = (
        Rule(
            LinkExtractor(allow=allowed_urls),  # Uses loaded allowed URLs
            callback='parse_item',
            follow=True
        ),
    )

    custom_settings = {
        'DOWNLOAD_DELAY': random.uniform(0.5, 1),
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [429, 500, 502, 503, 504],
        'CONCURRENT_REQUESTS': 32,
        'REDIRECT_ENABLED': True,
        'REDIRECT_MAX_TIMES': 15,
        'DOWNLOAD_TIMEOUT': 300,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'COOKIES_ENABLED': False,
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
        'LOG_STDOUT': True,
        'DEPTH_LIMIT': 5,  # Increase depth limit to 5
        'OFFSITE_ENABLED': True
    }

    def __init__(self, *args, **kwargs):
        super(APcdLinkSpider, self).__init__(*args, **kwargs)
        self.download_dir = 'download/onbase_links'
        os.makedirs(self.download_dir, exist_ok=True)
        # Open the file in 'w' mode to overwrite it each time
        self.file = open(self.download_dir + '/onbase_link.csv', 'w', newline='', encoding='utf-8')
        self.csvWriter = csv.writer(self.file)

    def parse_item(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all anchor tags
        anchor_tags = soup.find_all('a')

        # Iterate over each anchor tag and extract attributes and content
        for tag in anchor_tags:
            href = tag.get('href')  # Extract the href attribute
            content = tag.text.strip()  # Extract and clean the content inside the tag
            if href:
                # If href is a relative URL, make it absolute
                href = response.urljoin(href)

                # Check if the link contains 'hylandcloud' (case insensitive)
                if 'hylandcloud' in href.lower():
                    url = response.url
                    title = soup.title.string.strip() if soup.title else 'No Title'
                    # Log the link if it belongs to the allowed domain
                    self.logger.info(f'{title},{content},{href},{url}')
                    self.csvWriter.writerow([title, content, href, url])

    def handle_error(self, failure):
        # Log all errors and handle retries with exponential backoff
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}", level=logging.ERROR)
