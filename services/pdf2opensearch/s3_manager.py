import logging
import boto3
import json
from typing import List, Optional
from botocore.exceptions import BotoCoreError, ClientError

class S3Manager:
    """
    Manages S3 operations including listing objects in a folder and uploading documents.
    """

    def __init__(self, region_name: Optional[str] = None, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the S3Manager.

        :param region_name: AWS region for S3 operations. If None, uses the default region.
        :param logger: Optional logger instance. If None, a default logger is used.
        """
        self.s3 = boto3.client('s3', region_name=region_name)
        self.logger = logger or self._get_logger()

    def _get_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def list_objects(self, bucket_name: str, folder: str, exclude_extensions: List[str] = None) -> List[str]:
        """
        List all objects in an S3 folder, excluding files with certain extensions.

        :param bucket_name: Name of the S3 bucket.
        :param folder: The folder (prefix) to list objects under.
        :param exclude_extensions: List of file extensions to exclude (e.g., ['.json']).
        :return: A list of object keys under the specified folder.
        """
        exclude_extensions = exclude_extensions or []
        paginator = self.s3.get_paginator('list_objects_v2')
        response_iterator = paginator.paginate(Bucket=bucket_name, Prefix=folder)

        object_keys = []
        for page in response_iterator:
            for obj in page.get('Contents', []):
                key = obj['Key']
                if not any(key.endswith(ext) for ext in exclude_extensions):
                    object_keys.append(key)

        self.logger.info(f"Found {len(object_keys)} objects under folder: {folder}, excluding extensions: {exclude_extensions}")
        return object_keys

    def upload_document(self, document: dict, bucket_name: str, object_key: str) -> None:
        """
        Upload a JSON document to an S3 bucket.

        :param document: The JSON-serializable dictionary to upload.
        :param bucket_name: The name of the S3 bucket to upload to.
        :param object_key: The S3 object key (path) where the document will be stored.
        :raises RuntimeError: If the S3 upload fails.
        """
        try:
            json_data = json.dumps(document).encode('utf-8')
            self.s3.put_object(Bucket=bucket_name, Key=object_key, Body=json_data, ContentType='application/json')
            self.logger.info(f"Uploaded document to s3://{bucket_name}/{object_key}")
        except (BotoCoreError, ClientError) as e:
            self.logger.error(f"Failed to upload document to s3://{bucket_name}/{object_key}", exc_info=True)
            raise RuntimeError("Failed to upload document to S3") from e
