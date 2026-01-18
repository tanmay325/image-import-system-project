from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from flask import current_app
import io
import re

class GoogleDriveService:
    def __init__(self):
        self.api_key = current_app.config.get('GOOGLE_API_KEY')
        
    def extract_folder_id(self, folder_url):
        """Extract folder ID from Google Drive URL"""
        patterns = [
            r'folders/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, folder_url)
            if match:
                return match.group(1)
        
        
        return folder_url.strip()
    
    def list_images_in_folder(self, folder_id):
        """List all images in a Google Drive folder"""
        try:
            service = build('drive', 'v3', developerKey=self.api_key)
            
            query = f"'{folder_id}' in parents and (mimeType contains 'image/')"
            
            results = service.files().list(
                q=query,
                pageSize=100,
                fields="files(id, name, size, mimeType, webContentLink)"
            ).execute()
            
            files = results.get('files', [])
            return files
        except Exception as e:
            raise Exception(f"Error fetching files from Google Drive: {str(e)}")
    
    def download_file(self, file_id):
        """Download a file from Google Drive"""
        try:
            service = build('drive', 'v3', developerKey=self.api_key)
            
            request = service.files().get_media(fileId=file_id)
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_buffer.seek(0)
            return file_buffer
        except Exception as e:
            raise Exception(f"Error downloading file from Google Drive: {str(e)}")
