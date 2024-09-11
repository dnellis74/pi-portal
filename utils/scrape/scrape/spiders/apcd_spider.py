import logging
import os
from bs4 import BeautifulSoup
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import magic
from urllib.parse import urlparse
import re
import random  # For random delay
from datetime import datetime  # For timestamped logs
import json # for dumping dicts

from selenium_downloader import SeleniumDownloader

class ApcdSpider(CrawlSpider):
    name = 'apcd'
    json_path = '../../public/apcd_domains.json'

    # Load allowed domains and allowed URLs from the JSON file
    with open(json_path, 'r') as f:
        config = json.load(f)
    allowed_domains = config.get("allowed_domains", [])
    start_urls = config.get("start_urls", [])

    rules = (
        Rule(LinkExtractor(
                allow=r'https://oitco\.hylandcloud\.com/.*',
                deny=(),
                allow_domains=('oitco.hylandcloud.com',),
                deny_domains=(),
                restrict_xpaths=(),
                tags=('a', 'area'),
                attrs=('href',),
                canonicalize=True,
            ),
            callback='onbase_link',
            follow=True),
        Rule(LinkExtractor(
                allow=r'https://docs\.google\.com/.*',
                deny=(),
                allow_domains=('docs.google.com',),
                deny_domains=(),
                restrict_xpaths=(),
                tags=('a', 'area'),
                attrs=('href',),
                canonicalize=True,
            ),
            callback='google_link',
            follow=True),
        Rule(LinkExtractor(),
            callback='parse_item',
            follow=True),
    )
    # Optimized settings for better performance
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
        'DEPTH_LIMIT': 0,
        'OFFSITE_ENABLED': True
    } 

    def __init__(self, *args, **kwargs):
        super(ApcdSpider, self).__init__(*args, **kwargs)
        self.download_dir = 'download/apcd_' + datetime.now().strftime('%Y%m%d_%H%M%S')
        self.selenium = SeleniumDownloader(self.download_dir)

    def google_link(self, response):
        try:
            self.selenium.download_google_url(response.url)
        except Exception as e:
            self.log(f'Error downloading {response.url}: {e}', logging.ERROR)
        yield {'status': 'crawled', 'type': 'google', 'url': (response.url)}
            
    def onbase_link(self, response):
        try:
            self.selenium.download_onbase_pdf(response.url)
        except Exception as e:
            self.log(f'Error downloading {response.url}: {e}', logging.ERROR)
        yield {'status': 'success', 'type': 'onbase', 'url': (response.url)}


    def parse_item(self, response):
        # Generate a meaningful file name from the document information
        soup = BeautifulSoup(response.text, 'html.parser')
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
        try:
            with open(file_path, 'wb') as f:
                f.write(response.body)
        except FileExistsError:
            self.log(f'File already exists: {file_path}', logging.ERROR)
            return
        except OSError as e:
            self.log(f'OS error occurred while saving {file_path}: {e}', logging.ERROR)
            return

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
                self.log(f'OS error occurred while renaming {file_path} to {new_file_path}: {e}', logging.IFNO)
                return

        self.log(f'Saved [{response.url}] to [{new_file_path}]', logging.INFO)
        yield {'status': 'success', 'type': 'html', 'url': (response.url)}

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
