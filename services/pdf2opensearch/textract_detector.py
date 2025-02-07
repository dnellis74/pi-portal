import boto3
import time
import logging
import os
import json
from botocore.exceptions import BotoCoreError, ClientError
from typing import List, Optional

class TextractDocumentTextDetector:
    """
    A class for extracting text from documents stored in S3 using Amazon Textract's
    asynchronous APIs. Includes caching, pagination, and error handling.
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
        self.logger = self._get_logger()
        self.cache_dir = os.path.join("cache", self.document_key.replace("/", "_"))

    def _get_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _get_cache_filename(self, page_number: int) -> str:
        """
        Generate a cache file name based on the document key and page number.

        :param page_number: The page number (starting from 1).
        :return: The cache file name.
        """
        return os.path.join(self.cache_dir, f"page_{page_number}.json")

    def _ensure_cache_dir(self):
        """
        Ensure that the cache directory for this document key exists.
        """
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

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

    def _poll_for_completion(self, job_id: Optional[str]) -> List[str]:
        """
        Poll the Textract service until the job completes, then return the extracted lines.

        Implements a crude cache mechanism by saving responses to disk and reusing them
        if already available. Cache files are named based on page numbers.

        :param job_id: The Textract job ID, or None if using cached results exclusively.
        :return: List of extracted text lines from all pages.
        :raises RuntimeError: If the job fails or does not complete in time.
        """
        lines = []
        next_token = None  # Start with the initial response
        page_number = 1
        is_cache_mode = job_id is None  # Determine if we're exclusively using cached results

        # Ensure cache directory exists
        self._ensure_cache_dir()

        while True:
            try:
                cache_filename = self._get_cache_filename(page_number=page_number)

                if os.path.exists(cache_filename):
                    self.logger.info(f"Loading cached response from {cache_filename}")
                    with open(cache_filename, "r") as cache_file:
                        response = json.load(cache_file)
                    next_token = response.get("NextToken")  # Retrieve the NextToken from the cache
                elif not is_cache_mode:  # Only make live API calls if not in cache mode
                    # Make a Textract API call
                    if next_token:
                        response = self.textract.get_document_text_detection(JobId=job_id, NextToken=next_token)
                    else:
                        response = self.textract.get_document_text_detection(JobId=job_id)

                    # Cache the response if successful
                    if response.get("JobStatus") == "SUCCEEDED":
                        with open(cache_filename, "w") as cache_file:
                            json.dump(response, cache_file)
                    elif response.get("JobStatus") == "FAILED":
                        self.logger.error("Text detection job failed.")
                        raise RuntimeError("Text detection job failed.")
                    elif response.get("JobStatus") == "IN_PROGRESS":
                        self.logger.debug(f"Job {job_id} status: IN_PROGRESS. Waiting {self.delay}s before retrying...")
                        time.sleep(self.delay)
                        continue  # Skip processing and retry

                    next_token = response.get("NextToken")
                else:
                    # No cache file and not allowed to make live API calls
                    self.logger.info(f"No cache file found for page {page_number}, ending loop.")
                    break

                # Process the response
                blocks = response.get("Blocks", [])
                for block in blocks:
                    if block.get("BlockType") == "LINE":
                        lines.append(block.get("Text", ""))

                # Check for NextToken to paginate
                if not next_token:
                    self.logger.info("Reached the end of available pages.")
                    break  # No more pages
                page_number += 1  # Increment page number for the next cache file
            except (BotoCoreError, ClientError) as e:
                self.logger.error("Error retrieving Textract results", exc_info=True)
                raise RuntimeError("Error retrieving Textract results") from e

        if not lines:
            self.logger.error("No lines extracted from Textract response.")
        return lines

    def extract_text(self) -> List[str]:
        """
        Initiate the asynchronous text detection job or reuse cached results.
        Then retrieve and return all detected text lines.

        :return: List of extracted text lines.
        :raises RuntimeError: If the job fails or cannot be started.
        """
        # Check if the first cache file already exists
        initial_cache_filename = self._get_cache_filename(page_number=1)
        if os.path.exists(initial_cache_filename):
            self.logger.info("Cache detected for initial Textract response. Skipping job initiation.")
            return self._poll_for_completion(job_id=None)  # Pass `None` to skip re-initiation

        # Start the Textract job and poll for results
        job_id = self._start_document_text_detection()
        return self._poll_for_completion(job_id=job_id)
