from pathlib import Path

import scrapy
import json
import scrapy.utils
import validators
import os
import magic
from urllib.parse import urlparse
import logging

class RegsSpider(scrapy.Spider):
    name = "regs"

    def start_requests(self):

        # Read URLs from the JSON file
        with open('../../public/documents.json', 'r') as f:
            documents = json.load(f)

        # Create request
        for doc in documents:
            if doc['State'] == 'XXXX':
                 logging.info("Only " + doc['State'])
                 continue
            if 'Link' in doc and doc['Link']:
                if validators.url(doc['Link'], strict_query=False):
                    yield scrapy.Request(url=doc['Link'], callback=self.parse)
                else:
                    logging.error(doc['Description'] + " has invalid link " + doc['Link'])
            else:
                logging.error(doc['Description'] + " has no link")

    def parse(self, response):
        # Get the filename without the query string
        parsed_url = urlparse(response.url)
        filename = parsed_url.path.rstrip('/').split('/')[-1]

        # Create a subdirectory named after the domain
        domain_directory = os.path.join("download/", parsed_url.netloc)
        os.makedirs(domain_directory, exist_ok=True)

        # Check if the file already exists and generate a unique filename if needed
        file_path = os.path.join(domain_directory, parsed_url.netloc + "-" + filename)
        file_path = self.get_unique_filename(file_path)            
        
        # Save the response body
        with open(file_path, 'wb') as f:
            f.write(response.body)
        
        mime_type = self.mime_type(file_path)
        # make it a pdf, if it's a poorly named pdf
        if (not file_path.endswith('.pdf') and mime_type == 'application/pdf'):
            os.rename(file_path, file_path + '.pdf')

        if (not file_path.endswith('.doc') and mime_type == 'application/msword'):
            os.rename(file_path, file_path + '.doc')

        if (not file_path.endswith('.html') and mime_type == 'text/html'):
            os.rename(file_path, file_path + '.html')
            
        self.log(f'Saved file {filename}')

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
