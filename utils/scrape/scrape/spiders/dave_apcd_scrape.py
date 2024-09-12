from datetime import datetime
import logging
import os
import json
import re
from urllib.parse import urlparse
import magic
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
import random

from selenium_downloader import SeleniumDownloader


class ApcdScrape(CrawlSpider):
    name = "apcd_scrape"
    
    # Load allowed domains and allowed URLs from the JSON file
    with open(r'../../public/apcd_domains.json', 'r') as f:
        config = json.load(f)

    # Ensure the keys are in the JSON
    allowed_domains = config.get('allowed_domains', [])
    allowed_urls = config.get("allowed_urls", [])
    start_urls = ["https://cdphe.colorado.gov/apcd"]  # Start at the parent domain

    # Rule to only follow links that match the allowed URLs
    rules = (
        Rule(
            LinkExtractor(allow=allowed_urls),  # Uses loaded allowed URLs
            callback='parse',
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
        'COOKIES_ENABLED': True,
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
        'LOG_STDOUT': True,
        'DEPTH_LIMIT': 0,  # Increase depth limit to 5
        'OFFSITE_ENABLED': True
    }


    def __init__(self, *args, **kwargs):
        super(ApcdScrape, self).__init__(*args, **kwargs)
        self.download_dir = 'download/apcd_' + datetime.now().strftime('%Y%m%d_%H%M%S')
        self.selenium = SeleniumDownloader(self.download_dir)
        os.makedirs(self.download_dir, exist_ok=True)

    def parse(self, response):
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            self.save_html(soup, response)

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
                    if 'hylandcloud' in href:
                        self.selenium.download_onbase_pdf(href)
                    elif 'google' in href:
                        self.selenium.download_google_url(href)
            yield { 'status': 'success',  'url': (response.url)}
        except Exception as e:
            yield { 'status': 'failure',  'url': (response.url)}
        
    def save_html(self, soup, response):
        # Generate a meaningful file name from the document information
        title = soup.title.string
        base_filename = title

        # Create a subdirectory named after the domain
        parsed_url = urlparse(response.url)
        domain_directory = os.path.join(self.download_dir, parsed_url.netloc)
        os.makedirs(domain_directory, exist_ok=True)
        # Create the full file path with the new base filename
        file_path = os.path.join(domain_directory, base_filename)
        file_path = self.get_unique_filename(file_path)            

        # Save the response body
        with open(file_path, 'wb') as f:
            f.write(response.body)


        mime_type = self.mime_type(file_path)

        # Rename files based on MIME type with unique name check
        new_file_path = file_path
        if not file_path.endswith('.pdf') and mime_type == 'application/pdf':
            new_file_path = file_path + '.pdf'
        elif not file_path.endswith('.doc') and mime_type == 'application/msword':
            new_file_path = file_path + '.doc'
        elif not file_path.endswith('.html') and mime_type == 'text/html':
            new_file_path = file_path + '.html'
        
        # Check if new file path exists and generate a unique name
        new_file_path = self.get_unique_filename(new_file_path)

        # Rename the file
        if new_file_path != file_path:
            try:
                os.rename(file_path, new_file_path)
            except FileExistsError:
                self.log(f'File rename error: {new_file_path} already exists.', logging.ERROR)
                return
            except OSError as e:
                self.log(f'OS error occurred while renaming {file_path} to {new_file_path}: {e}', logging.ERROR)
                return

        self.log(f'Saved [{response.url}] to [{new_file_path}]', logging.INFO)

    def create_filename(self, doc_info):
        # Combine relevant fields to create a meaningful filename
        filename = f'{doc_info['State']}_{doc_info['Regulation']}_{doc_info['updated']}'
        # Sanitize the filename by removing or replacing any illegal characters
        filename = re.sub(r"[\\/*?:'<>|]", '_', filename)
        return filename

    def get_unique_filename(self, file_path):
        base, ext = os.path.splitext(file_path)
        count = 1
        while os.path.exists(file_path):
            file_path = f'{base}_{count}{ext}'
            count += 1
        return file_path

    def mime_type(self, file_path):
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
    