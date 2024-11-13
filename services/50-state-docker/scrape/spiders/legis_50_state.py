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

from items import PageContentItem  # For random delay

class LegisSpider(scrapy.Spider):
    name = "legis"

    def __init__(self, legis_file=None, job_folder=None, *args, **kwargs):
        super(LegisSpider, self).__init__(*args, **kwargs)
        self.parent_logger = logging.getLogger('scraper')

        # Initialize the S3 client
        self.s3_client = boto3.client('s3')
        

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
                #if not doc['jurisdiction'].__contains__('Colorado'):
                #    continue
                url = doc['url']
                if validators.url(url):
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_file,
                        meta={'title': doc['title'], 'jurisdiction': doc['jurisdiction']}
                    )                    
                else:
                    self.parent_logger.error(f'invalid url [{url}]')
        except Exception as e:
            self.parent_logger.error(e)            
        
    def parse_file(self, response):
        self.parent_logger.info(f"Visited {response.url}")
        try:
            # Get document information from meta data
            leg_title = response.meta['title']
            leg_jurisdiction = response.meta['jurisdiction']
            leg_domain = response.meta['download_slot']

            # Generate a meaningful file name from the document information
            base_filename = self.create_filename(leg_title, leg_jurisdiction)

            # Create the full file path with the new base filename
            file_path = os.path.join(leg_domain, base_filename)

            # Rename files based on MIME type with unique name check
            mime_type = self.mime_type(response.body)
            new_file_path = file_path
            if not file_path.endswith('.pdf') and mime_type == 'application/pdf':
                new_file_path = file_path + '.pdf'
            elif not file_path.endswith('.doc') and mime_type == 'application/msword':
                new_file_path = file_path + '.doc'
            elif not file_path.endswith('.html') and mime_type == 'text/html':
                new_file_path = file_path + '.html'

            item = PageContentItem()
            item['source_url'] = response.url
            item['content'] = response.body  # raw content
            item['key'] = new_file_path
            item['title'] = leg_title
            item['jurisdiction'] = leg_jurisdiction
            yield item
        except Exception as e:
            logging.error(f"Error processing {response.url}: {e}")

    def create_filename(self, title, jurisdiction):
        # Combine relevant fields to create a meaningful filename
        filename = f"{jurisdiction}_{title}"
        # Sanitize the filename by removing or replacing any illegal characters
        filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
        return filename

    def mime_type(self, buffer):
        return self.mimeDetector.from_buffer(buffer)
    
    def put_object(self, bucket_name, object_name, body, metadata=None):
        # Upload the data
        self.s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=body, Metadata=metadata)
        
    def read_from_s3(self, bucket_name, object_name):
        # Read the object from S3
        response = self.s3_client.get_object(Bucket=bucket_name, Key=object_name)
        payload = response['Body'].read()
        return json.loads(payload)
