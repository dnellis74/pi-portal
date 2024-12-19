import json
import logging
from typing import Dict, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

class S3Uploader:
    """
    Handles uploading a JSON document to an S3 bucket.
    """

    def __init__(self, 
                 region_name: Optional[str] = None,
                 logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the S3Uploader.

        :param region_name: AWS region for S3. If None, uses default region.
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

    def upload_doc(self, 
                   document: Dict[str, object], 
                   bucket_name: str, 
                   object_key: str) -> None:
        """
        Upload the given document as a JSON file to the specified S3 bucket.

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
            self.logger.error("Failed to upload document to S3", exc_info=True)
            raise RuntimeError("Failed to upload document to S3") from e
