import boto3
import requests
import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv
from botocore.exceptions import ProfileNotFound
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class MayanS3Sync:
    def __init__(self, aws_profile='default'):
        # Initialize S3 client using AWS credentials file
        try:
            session = boto3.Session(profile_name=aws_profile)
            self.s3 = session.client('s3')
        except ProfileNotFound:
            logger.warning(f"AWS profile '{aws_profile}' not found in ~/.aws/credentials")
            logger.warning("Using default credentials provider chain...")
            self.s3 = boto3.client('s3')
        
        # Mayan EDMS settings
        self.mayan_url = os.getenv('MAYAN_API_URL', 'http://18.237.103.111')
        self.mayan_token = os.getenv('MAYAN_API_TOKEN', '8c9ad3d7718df0753afb3d250b84258a3b72f509')
        self.headers = {
            'Authorization': f'Token {self.mayan_token}'
        }
        
        # S3 settings
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'sbx-colorado-only')
        self.folder_path = os.getenv('S3_FOLDER_PATH', 'Colorado')
        
        # Colorado cabinet ID in Mayan
        self.cabinet_id = os.getenv('MAYAN_COLORADO_CABINET_ID', '1')
        
        # Types to skip
        self.skip_types = set()  # Empty set, no types to skip

        # Add tracking for document processing times
        self.processing_times = []
        self.min_pause_ms = 250  # minimum 0.25 seconds

        # Validate required environment variables
        self._validate_config()

    def _validate_config(self):
        """Validate that all required environment variables are set with valid values"""
        if not self.mayan_url.startswith(('http://', 'https://')):
            raise ValueError('MAYAN_API_URL must be a valid HTTP/HTTPS URL')
        
        if len(self.mayan_token) < 8:
            raise ValueError('MAYAN_API_TOKEN must be at least 8 characters long')
        
        if not self.bucket_name or self.bucket_name == 'default-bucket':
            raise ValueError('S3_BUCKET_NAME must be configured')

    def get_document_type_id(self, type_name: str) -> Optional[int]:
        """Get document type ID from Mayan; create if it doesn't exist."""
        try:
            # Check if document type exists
            response = requests.get(
                f'{self.mayan_url}/api/v4/document_types/',
                headers=self.headers
            )
            response.raise_for_status()  # Raise an exception for HTTP errors

            for doc_type in response.json().get('results', []):
                if doc_type['label'] == type_name:
                    return doc_type['id']

            # Document type does not exist; attempt to create it
            create_response = requests.post(
                f'{self.mayan_url}/api/v4/document_types/',
                headers=self.headers,
                json={'label': type_name}
            )
            create_response.raise_for_status()  # Raise an exception for HTTP errors

            return create_response.json().get('id')

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get or create document type '{type_name}': {e}")
            return None

    def calculate_average_processing_time(self) -> float:
        """Calculate the average processing time from recent documents"""
        if not self.processing_times:
            return 2.0  # Default to 2 seconds if no data
        return sum(self.processing_times) / len(self.processing_times)

    def get_dynamic_pause_ms(self) -> int:
        """Calculate dynamic pause time based on average processing time"""
        avg_time = self.calculate_average_processing_time()
        # Convert to milliseconds and add buffer
        return int(avg_time * 1000) + self.min_pause_ms

    def update_processing_times(self, elapsed_time: float):
        """Update the running list of processing times"""
        self.processing_times.append(elapsed_time)
        # Keep only last 10 times to be adaptive
        if len(self.processing_times) > 10:
            self.processing_times.pop(0)

    def wait_for_document_ready(self, document_id: int, max_attempts: int = 10, initial_pause_ms: Optional[int] = None) -> bool:
        """Wait for document to be fully processed by polling its status"""
        
        # Use dynamic pause if not explicitly specified
        if initial_pause_ms is None:
            initial_pause_ms = self.get_dynamic_pause_ms()
        
        # Initial pause to allow processing to begin
        logger.debug(f"Initial pause of {initial_pause_ms}ms before checking document {document_id} status...")
        time.sleep(initial_pause_ms / 1000)
        start_time = time.time()

        for attempt in range(max_attempts):
            response = requests.get(
                f'{self.mayan_url}/api/v4/documents/{document_id}/',
                headers=self.headers
            )
            
            if not response.ok:
                logger.error(f"Failed to check document status: {response.text}")
                return False
            
            doc_data = response.json()
            if doc_data.get('file_latest'):
                elapsed_time = time.time() - start_time
                logger.info(f"Document {document_id} ready after {elapsed_time:.2f} seconds ({attempt + 1} attempts)")
                self.update_processing_times(elapsed_time)
                return True
                
            logger.info(f"Document {document_id} still processing (attempt {attempt + 1}/{max_attempts}, elapsed: {time.time() - start_time:.2f}s)...")
            time.sleep(1)
            
        elapsed_time = time.time() - start_time
        logger.error(f"Document {document_id} failed to process after {max_attempts} attempts ({elapsed_time:.2f} seconds)")
        return False

    def upload_document(self, file_key: str, document_type_id: int):
        """Upload document to Mayan"""
        try:
            # Download file from S3
            response = self.s3.get_object(Bucket=self.bucket_name, Key=file_key)
            file_content = response['Body'].read()
            filename = file_key.split('/')[-1]
            
            # Upload to Mayan using the upload endpoint
            files = {
                'document_type_id': (None, str(document_type_id)),
                'file': (filename, file_content)
            }
            
            upload_response = requests.post(
                f'{self.mayan_url}/api/v4/documents/upload/',
                headers=self.headers,
                files=files
            )
            
            if not upload_response.ok:
                logger.error(f"Failed to upload document {file_key}: {upload_response.text}")
                return
            
            document_id = upload_response.json()['id']
            
            # Wait for document to be ready
            if not self.wait_for_document_ready(document_id):
                return
            
            # Add to Colorado cabinet using the correct endpoint
            cabinet_response = requests.post(
                f'{self.mayan_url}/api/v4/cabinets/{self.cabinet_id}/documents/add/',
                headers=self.headers,
                json={'document': str(document_id)}
            )
            
            if not cabinet_response.ok:
                logger.error(f"Failed to add document to cabinet: {cabinet_response.text}")
                return
            
            logger.info(f"Successfully uploaded {filename} (ID: {document_id})")
            
        except Exception as e:
            logger.error(f"Error uploading {file_key}: {str(e)}")

    def document_exists(self, filename: str) -> bool:
        """Check if document already exists in Mayan by filename"""
        response = requests.get(
            f'{self.mayan_url}/api/v4/documents/',
            headers=self.headers,
            params={'label': filename}
        )
        
        if not response.ok:
            logger.error(f"Failed to check for existing document: {response.text}")
            return False
            
        results = response.json()['results']
        for doc in results:
            if doc['label'] == filename:
                return True
                
        return False

    def process_s3_folder(self, batch_size=100):
        """Process files in S3 folder in batches"""
        paginator = self.s3.get_paginator('list_objects_v2')
        processed_count = 0
        skipped_count = 0
        
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=self.folder_path):
            for obj in page.get('Contents', []):
                file_key = obj['Key']
                
                # Skip metadata files
                if file_key.endswith('.metadata.json'):
                    continue
                
                # Get metadata first to check aq_type
                json_key = f"{file_key}.metadata.json"
                try:
                    # Get metadata from JSON file
                    json_response = self.s3.get_object(
                        Bucket=self.bucket_name,
                        Key=json_key
                    )
                    json_data = json.loads(json_response['Body'].read().decode('utf-8'))
                    
                    # Get metadata from Attributes object
                    metadata = json_data.get('Attributes', {})
                    
                    # Get and clean aq_type from metadata
                    aq_type = metadata.get('aq_type', '').strip()
                    if not aq_type:
                        logger.warning(f"Skipping {file_key}: No aq_type in metadata")
                        continue
                    
                    # Skip specified document types
                    if aq_type in self.skip_types:
                        skipped_count += 1
                        logger.info(f"Skipping {file_key}: aq_type '{aq_type}' is in skip list (skipped: {skipped_count})")
                        continue
                    
                    filename = file_key.split('/')[-1]
                    
                    # Check if document already exists
                    if self.document_exists(filename):
                        skipped_count += 1
                        logger.info(f"Skipping {file_key}: Already exists in Mayan (skipped: {skipped_count})")
                        continue
                    
                    # Get or create document type
                    doc_type_id = self.get_document_type_id(aq_type)
                    
                    # Upload document
                    self.upload_document(file_key, doc_type_id)
                    processed_count += 1
                    logger.info(f"Processed {file_key} with type {aq_type} ({processed_count}/{batch_size})")
                    
                    if processed_count >= batch_size:
                        logger.info(f"\nBatch limit of {batch_size} reached. Stopping processing.")
                        logger.info(f"Total documents skipped (already existed): {skipped_count}")
                        return
                    
                except self.s3.exceptions.NoSuchKey:
                    logger.warning(f"Skipping {file_key}: No metadata file found")
                    continue
                except json.JSONDecodeError:
                    logger.error(f"Skipping {file_key}: Invalid JSON metadata")
                    continue

    def delete_all_documents(self):
        """Delete all documents from Mayan"""
        while True:
            # Get list of documents
            response = requests.get(
                f'{self.mayan_url}/api/v4/documents/',
                headers=self.headers
            )
            
            if not response.ok:
                logger.error("Failed to get document list")
                break
                
            documents = response.json()['results']
            if not documents:
                logger.info("No more documents to delete")
                break
                
            # Delete each document
            for doc in documents:
                delete_response = requests.delete(
                    f'{self.mayan_url}/api/v4/documents/{doc["id"]}/',
                    headers=self.headers
                )
                if delete_response.ok:
                    logger.info(f"Deleted document {doc['id']}")
                else:
                    logger.error(f"Failed to delete document {doc['id']}")
            
            # Wait for deletions to complete
            logger.info("Waiting for deletions to complete...")
            time.sleep(2)  # Give Mayan time to process deletions
            
            # Verify documents are gone
            verify_response = requests.get(
                f'{self.mayan_url}/api/v4/documents/',
                headers=self.headers
            )
            if verify_response.ok and len(verify_response.json()['results']) == 0:
                logger.info("All documents successfully deleted")
                break

if __name__ == "__main__":
    syncer = MayanS3Sync(aws_profile='default')
    logger.info("Processing new documents...")
    syncer.process_s3_folder(batch_size=5000)