import boto3
import time
import logging
from botocore.exceptions import BotoCoreError, ClientError
from typing import List, Optional

class TextractDocumentTextDetector:
    """
    A class for extracting text from documents stored in S3 using Amazon Textract's
    asynchronous APIs. This class follows Python's OO best practices and includes
    robust logging and error handling.
    """
    
    def __init__(self, 
                 bucket_name: str, 
                 document_key: str, 
                 region_name: Optional[str] = None,
                 max_retries: int = 60, 
                 delay: int = 5) -> None:
        """
        Initialize the TextractDocumentTextDetector.

        :param bucket_name: Name of the S3 bucket containing the document.
        :param document_key: Key (path) of the document in the S3 bucket.
        :param region_name: AWS region for Textract. If None, uses default region.
        :param max_retries: Maximum number of times to poll for completion.
        :param delay: Delay in seconds between polling attempts.
        """
        self.bucket_name = bucket_name
        self.document_key = document_key
        self.region_name = region_name
        self.max_retries = max_retries
        self.delay = delay
        
        self.textract = boto3.client('textract', region_name=self.region_name)

        # Configure logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(formatter)
        # Avoid adding multiple handlers if instantiated multiple times
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def extract_text(self) -> List[str]:
        """
        Initiate the asynchronous text detection and return the extracted text lines
        once the job has succeeded.

        :return: List of extracted text lines.
        :raises RuntimeError: If job fails or cannot be started.
        """
        job_id = self._start_document_text_detection()
        lines = self._poll_for_completion(job_id)
        return lines

    def _start_document_text_detection(self) -> str:
        """
        Start the asynchronous text detection job.

        :return: Job ID for the started text detection job.
        :raises RuntimeError: If the Textract API call fails.
        """
        try:
            response = self.textract.start_document_text_detection(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': self.bucket_name,
                        'Name': self.document_key
                    }
                }
            )
            job_id = response['JobId']
            self.logger.info(f"Started text detection job with ID: {job_id}")
            return job_id
        except (BotoCoreError, ClientError) as e:
            self.logger.error("Failed to start document text detection", exc_info=True)
            raise RuntimeError("Failed to start document text detection") from e

    def _poll_for_completion(self, job_id: str) -> List[str]:
        """
        Poll the Textract service until the job completes, then return the extracted lines.

        :param job_id: The Textract job ID.
        :return: List of extracted text lines.
        :raises RuntimeError: If the job fails or does not complete in time.
        """
        for attempt in range(self.max_retries):
            try:
                response = self.textract.get_document_text_detection(JobId=job_id)
            except (BotoCoreError, ClientError) as e:
                self.logger.error("Error retrieving text detection results", exc_info=True)
                raise RuntimeError("Error retrieving text detection results") from e
            
            status = response.get('JobStatus')
            if status == 'SUCCEEDED':
                self.logger.info("Text detection job succeeded.")
                lines = [block['Text'] for block in response.get('Blocks', []) if block['BlockType'] == 'LINE']
                return lines
            elif status == 'FAILED':
                self.logger.error("Text detection job failed.")
                raise RuntimeError("Text detection job failed.")
            else:
                self.logger.debug(f"Job {job_id} status: {status}. Waiting {self.delay}s before retrying...")
                time.sleep(self.delay)

        self.logger.error(f"Text detection job did not complete after {self.max_retries} attempts.")
        raise RuntimeError("Text detection job did not complete in time.")
