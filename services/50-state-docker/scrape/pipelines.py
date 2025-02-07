# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
import json
import mimetypes
from itemadapter import ItemAdapter

import boto3
from botocore.exceptions import ClientError
import logging
from urllib.parse import urlparse
from twisted.internet import threads

from items import PageContentItem
from s3_sanitize import sanitize_metadata, sanitize_s3_key

class S3Upload_Pipeline:
    def __init__(self, bucket_name, job_folder):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bucket_name = bucket_name
        self.job_folder = job_folder
        self.s3_client = boto3.client('s3')

    @classmethod
    def from_crawler(cls, crawler):
        bucket_name = crawler.settings.get('BUCKET_NAME')
        job_folder = crawler.settings.get('JOB_FOLDER')

        return cls(
            bucket_name,
            job_folder
        )

    def process_item(self, item, spider):
        # Use deferToThread to offload the blocking operation
        deferred = threads.deferToThread(self.s3_put_synch, item)
        # Add callbacks to handle success or error
        deferred.addCallback(self.handle_result, item, spider)
        deferred.addErrback(self.handle_error, item, spider)
        return deferred  # Return the Deferred to inform Scrapy
    
    def handle_result(self, result, item, spider):
        # This callback is called when the blocking operation completes successfully
        self.logger.debug(f"Successfully uploaded item: {item['source_url']}")
        return result  # Pass the item to the next stage

    def handle_error(self, failure, item, spider):
        # This errback is called if the blocking operation raises an exception
        self.logger.error(f"Error uploaded item: {item['source_url']}\nError: {failure}")
        # Decide how to handle the error: retry, drop the item, etc.
        # For this example, we'll just pass the failure along
        return failure

    def s3_put_synch(self, item:PageContentItem):
        composite_title = item['jurisdiction'] + " - " + item['title']
        if item['description'] != '':
            composite_title += " - " + item['description']
        # Create the key in steps because of forward slashes are both wanted, AND unwanted
        if item['mime_type'] and mimetypes.guess_extension(item['mime_type']):
            extension = mimetypes.guess_extension(item['mime_type']) or 'pdf'
        else:
            extension = 'pdf'
        sanitized_title = sanitize_s3_key(f"{composite_title}.{extension}")
        sanitized_jurisdiction = sanitize_s3_key(f"{item['jurisdiction']}")
        sanitized_key = f"{self.job_folder}/{sanitized_jurisdiction}/{sanitized_title}"
        attributes = sanitize_metadata({
            '_source_uri': item['source_url'],
            'pi_url': f"s3://{self.bucket_name}/{sanitized_key}",
            'jurisdiction': item['jurisdiction'],
            'title': item['title'],
            'description': item['description'],
            '_document_title': composite_title,
            'aq_type': item['doc_type'],
            'tombstone': item['tombstone'],
            'language': item['language']
        })
        sanitized_metadata = {
            'Attributes': attributes
        }
        json_str = json.dumps(sanitized_metadata, indent=2)
        metadata_utf8_json = json_str.encode('utf-8')
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=sanitized_key,
                Body=item['content'],
            )
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f'{sanitized_key}.metadata.json',
                Body=metadata_utf8_json,                
            )
            self.logger.info(f"Uploaded {item['source_url']} to S3 bucket {self.bucket_name} as {sanitized_key}")
        except ClientError as e:
            self.logger.error(f"Failed to upload {item['source_url']} to S3: {str(e)}")
        return item

    def get_object_key(self, item):
        # Use URL path as object key, defaulting to 'index.html' if necessary
        parsed_url = urlparse(item['source_url'])
        path = parsed_url.path.lstrip('/')
        if not path or path.endswith('/'):
            path += 'index.html'
        object_key = path
        return object_key
    
    
