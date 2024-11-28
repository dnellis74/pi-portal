from io import BytesIO
import traceback
import boto3
import scrapy
import json
import scrapy.http
import scrapy.utils
from scrapy.http import Response
import magic
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build
from google.oauth2 import service_account
from typing import List
from urllib.parse import urlparse


from items import PageContentItem  # For random delay

class LegisSpider(scrapy.Spider):
    name = "legis"

    def __init__(self, legis_file=None, job_folder=None, *args, **kwargs):
        super(LegisSpider, self).__init__(*args, **kwargs)
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
                if urlparse(url):
                    meta:dict ={
                        'jurisdiction': doc['jurisdiction'],
                        'title': doc['title'],
                        'description': doc.get('description', ''),
                        'doc_type': doc.get('doc_type', ''),
                        'tombstone': doc.get('tombstone', ''),
                        'language': doc.get('language', 'en')
                    }
                    if 'folders' in url:
                        folder_id = url.split('?')[0].rstrip('/').split('/')[-1]
                        meta["google_drive_folder_id"] = folder_id
                    yield scrapy.Request(
                        url=url,
                        meta=meta
                    )                    
                else:
                    self.logger.warning(f'invalid url [{url}]')
        except Exception as e:
            self.logger.error(e)            
        
    def parse(self, response:Response):
        self.logger.info(f"Parsing {response.url}")                
        try:           
            # Check if the response has Google Drive files
            if 'google_drive_folder' in response.meta:
                    items = self._download_drive_folder(response)
                    for item in items:
                        yield item
            elif 'google_drive_file' in response.meta:
                file_id = response.meta['google_drive_file']
                item = self._download_to_item(response, file_id)
                yield item
            else:
                # Rename files based on MIME type with unique name check
                mime_type = self.detect_mime(response.body)
                request:scrapy.Request = response.request
                item = self.build_item(
                    response.url,
                    request.url,
                    response.body,
                    response.meta['title'],
                    response.meta['description'],
                    response.meta['jurisdiction'],
                    response.meta['doc_type'],
                    response.meta['tombstone'],
                    response.meta['language'],
                    mime_type
                )
                yield item
        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {e}")
            self.logger.error("Stack trace:\n%s", traceback.format_exc())

    def rename_with_mime(self, file_path:str, mime_type):
        new_file_path = file_path
        if not file_path.endswith('.pdf') and mime_type == 'application/pdf':
            new_file_path = file_path + '.pdf'
        elif not file_path.endswith('.doc') and mime_type == 'application/msword':
            new_file_path = file_path + '.doc'
        elif not file_path.endswith('.html') and mime_type == 'text/html':
            new_file_path = file_path + '.html'
        return new_file_path

    def build_item(self, url, pi_url, content, title, description, jurisdiction, doc_type, tombstone, language, mime_type):
        item = PageContentItem()
        item['source_url'] = url
        item['pi_url'] = pi_url
        item['content'] = content  # raw content
        item['title'] = title
        item['description'] = description
        item['jurisdiction'] = jurisdiction
        item['doc_type'] = doc_type
        item['tombstone'] = tombstone
        item['language'] = language
        item['mime_type'] = mime_type
        return item

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
    
    def _download_drive_folder(self, response:scrapy.http.Response):
        files = response.meta['google_drive_files']
        items = List[item]
        # For each file, create a request to download the file content
        for file in files:            
            file_id = file['id']
            item = self._download_to_item(response, file_id)
            items.append(item)
        return items

    def _download_to_item(self, response:scrapy.http.Response, file_id):
        request = self._build_file_request(file_id)
        content = self._download_file_content(request)
        file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
        shareable_link = file.get('webViewLink')
        item = self.build_item(
                shareable_link,
                response.request.url,
                content,
                response.meta['title'],
                response.meta['description'],
                response.meta['jurisdiction'],
                response.meta['doc_type'],
                response.meta['tombstone'],
                response.meta['language'],
                file.get("mimeType")
            )
        return item
    