import os
import re
from scrapy.http import Response
from google.oauth2 import service_account
from googleapiclient.discovery import build

# This class catches google drive folder requests and turns them into file requests
class GoogleDriveMiddleware:
    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
        self.service = self._build_service()

    @classmethod
    def from_crawler(cls, crawler):
        credentials_path = crawler.settings.get('GOOGLE_DRIVE_CREDENTIALS_FILE')
        if not credentials_path or not os.path.exists(credentials_path):
            raise ValueError(
                "GOOGLE_DRIVE_CREDENTIALS_FILE setting is required and must point to a valid credentials file."
            )
        return cls(credentials_path)

    def _build_service(self):
        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=scopes
        )
        service = build('drive', 'v3', credentials=credentials)
        return service

    def process_request(self, request, spider):
        # Check if the URL is a Google Drive folder
        if 'drive.google.com' in request.url:
            if (folder_id := self._extract_folder_id(request.url)) != None:
                # List all files in the folder
                files = self._list_files_in_folder(folder_id)
                # Return a Response with the list of files in meta
                request.meta['google_drive_folder'] = files
                return Response(
                    url=request.url,
                    status=200,
                    request=request
                )
            elif (file_id := self._extract_file_id(request.url)) != None:
                request.meta['google_drive_file'] = file_id
                return Response(
                    url=request.url,
                    status=200,
                    request=request
                )
            else:
                # If folder ID is not found, ignore the request
                return Response(
                    url=request.url,
                    status=404,
                    request=request
                )
        # Wasnt a google link, continue
        return None


    def _extract_file_id(self, url):
        """
        Extracts the file ID from a Google Drive file URL.

        :param url: The Google Drive file URL
        :return: The extracted file ID or None if no match is found
        """
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
        return match.group(1) if match else None

    def _extract_folder_id(self, url):
        # Extract the folder ID using regex
        match = re.search(r'/folders/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        return None

    def _list_files_in_folder(self, folder_id):
        # List all files in the folder using Google Drive API
        query = f"'{folder_id}' in parents and trashed = false"
        results = self.service.files().list(
            q=query,
            fields="files(id, name, mimeType)"
        ).execute()
        files = results.get('files', [])
        return files
    

