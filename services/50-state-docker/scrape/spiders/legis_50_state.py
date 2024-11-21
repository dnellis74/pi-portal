from io import BytesIO
import logging
import boto3
import scrapy
import json
import scrapy.utils
import validators
import os
import magic
from urllib.parse import urlparse
import re
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build
from google.oauth2 import service_account

from items import PageContentItem  # For random delay

class LegisSpider(scrapy.Spider):
    name = "legis"

    def __init__(self, legis_file=None, job_folder=None, *args, **kwargs):
        super(LegisSpider, self).__init__(*args, **kwargs)
        self.parent_logger = logging.getLogger('scraper')
        self.credentials_path = './sbx-kendra-8e724bd9a0ce.json'

        # Initialize the S3 client
        self.s3_client = boto3.client('s3')
        
        self.service = self._build_service()
        self.mimeDetector = magic.Magic(mime=True)
        self.job_folder = job_folder
        
        # Read the dictionary from the file
        try:
            self.docs = self.read_from_s3('sbx-piai-docs', f'{job_folder}/{legis_file}')
        except Exception as e:
            raise Exception(f"Error reading file from S3: {e}")

    def _build_service(self):
        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=scopes
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
        
    def start_requests(self):
        try:
            # Iterate over the dictionary and create requests for each URL
            for doc in self.docs:
                url:str = doc['url']
                if validators.url(url):
                    meta:dict ={
                        'title': doc['title'],
                        'jurisdiction': doc['jurisdiction'],
                        'doc_type': doc['doc_type'],
                        'tombstone': doc['tombstone'],
                        'language': doc['language']
                    }
                    if 'folders' in url:
                        folder_id = url.split('?')[0].rstrip('/').split('/')[-1]
                        meta["google_drive_folder_id"] = folder_id
                    yield scrapy.Request(
                        url=url,
                        meta=meta
                    )                    
                else:
                    self.parent_logger.error(f'invalid url [{url}]')
        except Exception as e:
            self.parent_logger.error(e)            
        
    def parse(self, response):
        self.parent_logger.info(f"Visited {response.url}")                
        try:
            # Get document information from meta data
            leg_title = response.meta['title']
            leg_jurisdiction = response.meta['jurisdiction']
            leg_domain = response.meta['download_slot']
            doc_type = response.meta['doc_type']
            tombstone = response.meta['tombstone']
            language = response.meta['language']

            # Generate a meaningful file name from the document information
            base_filename = self.create_filename(leg_title, leg_jurisdiction)

            # Create the full file path with the new base filename
            file_path = os.path.join(leg_domain, base_filename)
            
            # Check if the response has Google Drive files
            if 'google_drive_files' in response.meta:
                files = response.meta['google_drive_files']
                # For each file, create a request to download the file content
                for file in files:
                    file_id = file['id']
                    mime_type = file['mimeType']
                    file_path = os.path.join(leg_domain, file['name'])
                    request = self._build_file_request(file_id)
                    content = self._download_file_content(request)
                    file = self.service.files().get(
                        fileId=file_id,
                        fields='webViewLink'
                    ).execute()
                    shareable_link = file.get('webViewLink')
                    new_file_path = self.rename_with_mime(file_path, mime_type)
                    item = self.build_item(shareable_link,
                        content,
                        leg_title,
                        leg_jurisdiction,
                        doc_type,
                        tombstone,
                        language,
                        new_file_path
                    )
                    yield item
            else:
                # Rename files based on MIME type with unique name check
                mime_type = self.detect_mime(response.body)
                new_file_path = self.rename_with_mime(file_path, mime_type)            

                item = self.build_item(response.url,
                    response.content,
                    leg_title,
                    leg_jurisdiction,
                    doc_type,
                    tombstone,
                    language,
                    new_file_path
                )
                yield item
        except Exception as e:
            logging.error(f"Error processing {response.url}: {e}")

    def rename_with_mime(self, file_path, mime_type):
        new_file_path = file_path
        if not file_path.endswith('.pdf') and mime_type == 'application/pdf':
            new_file_path = file_path + '.pdf'
        elif not file_path.endswith('.doc') and mime_type == 'application/msword':
            new_file_path = file_path + '.doc'
        elif not file_path.endswith('.html') and mime_type == 'text/html':
            new_file_path = file_path + '.html'
        return new_file_path

    def build_item(self, url, content, leg_title, leg_jurisdiction, doc_type, tombstone, language, new_file_path):
        item = PageContentItem()
        item['source_url'] = url
        item['content'] = content  # raw content
        item['key'] = new_file_path
        item['title'] = leg_title
        item['jurisdiction'] = leg_jurisdiction
        item['doc_type'] = doc_type
        item['tombstone'] = tombstone
        item['language'] = language
        return item

    def create_filename(self, title, jurisdiction):
        # Combine relevant fields to create a meaningful filename
        filename = f"{jurisdiction}_{title}"
        # Sanitize the filename by removing or replacing any illegal characters
        filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
        return filename

    def detect_mime(self, buffer):
        return self.mimeDetector.from_buffer(buffer)
    
    def put_object(self, bucket_name, object_name, body, metadata=None):
        # Upload the data
        self.s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=body, Metadata=metadata)
        
    def read_from_s3(self, bucket_name, object_name):
        # Read the object from S3
        response = self.s3_client.get_object(Bucket=bucket_name, Key=object_name)
        payload = response['Body'].read()
        return json.loads(payload)
    
    def _download_file_content(self, request):
        # Download file content using Google Drive API
        buffer = BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        buffer.seek(0)
        return buffer.read()
    
    def _build_file_request(self, file_id):
        # Build a request for a file from Google Drive API
        request = self.service.files().get_media(fileId=file_id)
        return request
