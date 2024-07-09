from pathlib import Path

import scrapy
import json
import validators

class RegsSpider(scrapy.Spider):
    name = "regs"

    def start_requests(self):

        # Read URLs from the JSON file
        with open('../public/documents.json', 'r') as f:
            documents = json.load(f)

        # Create request
        for doc in documents:
            if 'Link' in doc and doc['Link'] and validators.url(doc['Link']):
                yield scrapy.Request(url=doc['Link'], callback=self.parse)
            else:
                print(doc['Description'])

    def parse(self, response):
        # Extract the filename from the URL
        filename = response.url.split('/')[-1]
        if not filename:
            filename = 'index.html'
        
        # Save the response body
        with open("download/" + filename, 'wb') as f:
            f.write(response.body)
        
        self.log(f'Saved file {filename}')
