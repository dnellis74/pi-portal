# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import boto3
from botocore.exceptions import ClientError
import logging
from urllib.parse import urlparse
from twisted.internet import threads

class S3Upload:
    def __init__(self, bucket_name, job_folder):
        self.logger = logging.getLogger(__name__)
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

    def s3_put_synch(self, item):
        object_key = item['key']
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f'{self.job_folder}/{object_key}',
                Body=item['content'],
                Metadata={
                    'source_url': item['source_url'],
                    'jurisdiction': item['jurisdiction'],
                    'title': item['title']
                }
            )
            self.logger.info(f"Uploaded {item['source_url']} to S3 bucket {self.bucket_name} as {object_key}")
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
