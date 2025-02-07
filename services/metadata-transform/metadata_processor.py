import json
import logging
import traceback

import boto3

class MetadataProcessor:
    def __init__(self, bucket_name):
        self.logger = logging.getLogger(__name__)
        self.s3_client = boto3.client('s3')
        paginator = self.s3_client.get_paginator('list_objects_v2')
        self.page_iterator = paginator.paginate(Bucket=bucket_name)
        self.bucket_name = bucket_name
        
    def process_all_metadata_files(self):
        """
        Processes all metadata files in the S3 bucket.
        """
        total_files = 0
        altered_files = 0
        errors = []
        for page in self.page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    if self.is_metadata_file(key):
                        total_files += 1
                        try:
                            metadata = self.get_metadata_from_s3(key)
                            modified_metadata = self.process(metadata)
                            if modified_metadata:
                                self.write_metadata_to_s3(key, modified_metadata)
                                altered_files += 1
                            else:
                                self.logger.info(f"Metadata unchanged for {key}")
                        except Exception as e:
                            error_message = f"Error processing {key}: {str(e)}"
                            self.logger.error("Stack trace:\n%s", traceback.format_exc())
                            errors.append(error_message)
        return errors
        
    def process(self, metadata):
        """
        Override this method to perform custom transformations on the metadata.
        """
        # By default, do nothing
        return None

    def is_metadata_file(self, key):
        """
        Determines if the S3 object key corresponds to a metadata file.
        Modify the condition based on your metadata file naming conventions.
        """
        # Assuming metadata files end with '_metadata.json'
        return key.endswith('metadata.json')

    def get_metadata_from_s3(self, key):
        """
        Retrieves and loads the metadata JSON from S3.
        """
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        content = response['Body'].read().decode('utf-8')
        metadata = json.loads(content)
        return metadata

    def write_metadata_to_s3(self, key, metadata):
        """
        Writes the modified metadata back to S3.
        """
        content = json.dumps(metadata, indent=2)
        self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=content)
        