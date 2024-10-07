from pathlib import Path
import scrapy
import json
import scrapy.utils
import validators
import os
import shutil
import magic
from urllib.parse import urlparse
import logging
import re
import random  # For random delay
from datetime import datetime  # For timestamped logs

class RegsSpider(scrapy.Spider):
    name = "regs"

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
    }

    def __init__(self, *args, **kwargs):
        super(RegsSpider, self).__init__(*args, **kwargs)
        self.setup_logging()  # Setup logging with file and terminal output
        self.reset_download_folder()

    def setup_logging(self):
        # Setup logging with both file and terminal output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f'scrapy_output_{timestamp}.log'

        # Clear existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # File handler
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()  # Terminal output
            ]
        )

    def reset_download_folder(self):
        download_dir = "download"
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
        os.makedirs(download_dir)

    def start_requests(self):
        # Read URLs from the JSON file # Change file location
        data_path = '../../../../public/documents.json'
        with open(data_path, 'r') as f:
            documents = json.load(f)

        # Create requests
        for doc in documents:
            state = doc.get('State', 'Unknown')  # Extract state information
            if state == 'XXXX':
                logging.info("Only " + state)
                continue
            if 'Link' in doc and doc['Link']:
                if validators.url(doc['Link'], strict_query=False):
                    # Pass the document information to the callback
                    yield scrapy.Request(url=doc['Link'], callback=self.parse, meta={'doc_info': doc}, errback=self.handle_error)
                else:
                    self.log(f"{doc['Description']} has invalid link {doc['Link']} for state {state}", level=logging.ERROR)
            else:
                self.log(f"{doc['Description']} has no link for state {state}", level=logging.ERROR)

    def parse(self, response):
        # Get document information from meta data
        doc_info = response.meta['doc_info']

        # Generate a meaningful file name from the document information
        base_filename = self.create_filename(doc_info)

        # Create a subdirectory named after the domain
        parsed_url = urlparse(response.url)
        domain_directory = os.path.join("download/", parsed_url.netloc)
        os.makedirs(domain_directory, exist_ok=True)

        # Create the full file path with the new base filename
        file_path = os.path.join(domain_directory, base_filename)
        file_path = self.get_unique_filename(file_path)            

        # Save the response body
        try:
            with open(file_path, 'wb') as f:
                f.write(response.body)
        except FileExistsError:
            self.log(f"File already exists: {file_path}", level=logging.ERROR)
            return
        except OSError as e:
            self.log(f"OS error occurred while saving {file_path}: {e}", level=logging.ERROR)
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
                self.log(f"File rename error: {new_file_path} already exists.", level=logging.ERROR)
            except OSError as e:
                self.log(f"OS error occurred while renaming {file_path} to {new_file_path}: {e}", level=logging.ERROR)
                return

        self.log(f'Saved file {new_file_path}')

    def handle_error(self, failure):
        # Log all errors and handle retries with exponential backoff
        state = failure.request.meta['doc_info'].get('State', 'Unknown')
        self.log(f"Request failed: {failure.request.url} - {failure.value} for state {state}", level=logging.ERROR)

    def create_filename(self, doc_info):
        # Combine relevant fields to create a meaningful filename
        filename = f"{doc_info['State']}_{doc_info['Regulation']}_{doc_info['updated']}"
        # Sanitize the filename by removing or replacing any illegal characters
        filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
        return filename

    def get_unique_filename(self, file_path):
        base, ext = os.path.splitext(file_path)
        count = 1
        while os.path.exists(file_path):
            file_path = f"{base}_{count}{ext}"
            count += 1
        return file_path

    def mime_type(self, file_path):
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)


