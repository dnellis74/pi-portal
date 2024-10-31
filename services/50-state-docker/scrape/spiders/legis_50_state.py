import logging
import boto3
import scrapy
import json
import scrapy.utils
import validators
import os
import magic
from urllib.parse import urlparse
import re
import random  # For random delay

class LegisSpider(scrapy.Spider):
    name = "legis"

    # Optimized settings for better performance
    custom_settings = {
        'DOWNLOAD_DELAY': random.uniform(0.1, .5),  # Random delay between requests to reduce rate-limiting
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,  # Lower retries to avoid wasting time on persistent failures
        'RETRY_HTTP_CODES': [429, 500, 502, 503, 504], 
        # Retry on these HTTP errors
        'CONCURRENT_REQUESTS': 64,  # Adjust concurrency to balance speed and reliability
        'REDIRECT_ENABLED': True,
        'REDIRECT_MAX_TIMES': 10,
        'DOWNLOAD_TIMEOUT': 120,  # Increase timeout slightly for slower responses
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',  # Use a common user-agent
        'COOKIES_ENABLED': False,  # Disable cookies to avoid tracking
        'ROBOTSTXT_OBEY': False,  # Ignore robots.txt for comprehensive scraping
        'LOG_LEVEL': 'INFO',  # Log level
        'LOG_STDOUT': False,  # Log to stdout (terminal)
    }

    def __init__(self, legis_file=None, job_folder=None, log_file=None, *args, **kwargs):
        super(LegisSpider, self).__init__(*args, **kwargs)
        
        logging.getLogger().setLevel(logging.INFO)
        # Set logging level for boto3 and botocore
        logging.getLogger('boto3').setLevel(logging.INFO)
        logging.getLogger('botocore').setLevel(logging.INFO)
        # Optional: Set logging level for specific AWS service-related modules (like s3transfer)
        logging.getLogger('s3transfer').setLevel(logging.INFO)
        logging.getLogger('urllib3').setLevel(logging.INFO)
        logging.getLogger('scrapy').setLevel(logging.INFO)
        logging.getLogger('scrapy').addHandler(logging.FileHandler(log_file))

        
        # Initialize the S3 client
        self.s3_client = boto3.client('s3')
        
        self.bucket_name = 'sbx-piai-docs'
        self.mimeDetector = magic.Magic(mime=True)
        self.job_folder = job_folder

        # Read the dictionary from the file
        try:
            self.docs = self.read_from_s3('sbx-piai-docs', f'{job_folder}/{legis_file}')
        except Exception as e:
            raise Exception(f"Error reading file from S3: {e}")

    def start_requests(self):
        try:
            # Iterate over the dictionary and create requests for each URL
            for doc in self.docs:
                url = doc['url']
                if validators.url(url):
                    yield scrapy.Request(url=url, callback=self.parse, meta={'name': doc['name'], 'state': doc['jurisdiction']})
                else:
                    self.logger.error(f'invalid url [{url}]')
        except Exception as e:
            self.logger.error(e)
        
    def parse(self, response):
        try:
            # Get document information from meta data
            leg_name = response.meta['name']
            leg_jurisdiction = response.meta['state']
            leg_domain = response.meta['download_slot']

            # Generate a meaningful file name from the document information
            base_filename = self.create_filename(leg_name, leg_jurisdiction)

            # Create a subdirectory named after the domain
            domain_directory = os.path.join(f"{self.job_folder}/{leg_domain}")

            # Create the full file path with the new base filename
            file_path = os.path.join(domain_directory, base_filename)

            # Rename files based on MIME type with unique name check
            mime_type = self.mime_type(response.body)
            new_file_path = file_path
            if not file_path.endswith('.pdf') and mime_type == 'application/pdf':
                new_file_path = file_path + '.pdf'
            elif not file_path.endswith('.doc') and mime_type == 'application/msword':
                new_file_path = file_path + '.doc'
            elif not file_path.endswith('.html') and mime_type == 'text/html':
                new_file_path = file_path + '.html'

            # Save the response body
            self.write_response_to_s3(self.bucket_name, new_file_path, response)

            return {'url': response.url, 'status': response.status}
        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {e}")


    def create_filename(self, name, jurisdiction):
        # Combine relevant fields to create a meaningful filename
        filename = f"{jurisdiction}_{name}"
        # Sanitize the filename by removing or replacing any illegal characters
        filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
        return filename

    def mime_type(self, buffer):
        return self.mimeDetector.from_buffer(buffer)
    
    def write_response_to_s3(self, bucket_name, object_name, response):
        # Upload the data
        self.s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=response.body)
        
    def read_from_s3(self, bucket_name, object_name):
        # Read the object from S3
        response = self.s3_client.get_object(Bucket=bucket_name, Key=object_name)
        payload = response['Body'].read()
        return json.loads(payload)
