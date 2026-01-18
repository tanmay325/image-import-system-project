from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import io
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import concurrent.futures
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

# Service URLs
STORAGE_SERVICE_URL = os.getenv('STORAGE_SERVICE_URL', 'http://storage-service:5003')
METADATA_SERVICE_URL = os.getenv('METADATA_SERVICE_URL', 'http://metadata-service:5002')
IMPORT_SERVICE_URL = os.getenv('IMPORT_SERVICE_URL', 'http://import-service:5001')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 'aws')


executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)

def download_from_google_drive(file_id):
    """Download file from Google Drive"""
    try:
        service = build('drive', 'v3', developerKey=GOOGLE_API_KEY)
        request_obj = service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request_obj)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file_buffer.seek(0)
        return file_buffer
    except Exception as e:
        raise Exception(f"Error downloading from Google Drive: {str(e)}")

def upload_to_storage(file_buffer, filename, mime_type):
    """Upload file to cloud storage via Storage Service"""
    import base64
    

    file_buffer.seek(0)
    file_data = base64.b64encode(file_buffer.read()).decode('utf-8')
    
    response = requests.post(
        f"{STORAGE_SERVICE_URL}/upload",
        json={
            'file_data': file_data,
            'filename': filename,
            'mime_type': mime_type,
            'provider': STORAGE_PROVIDER
        },
        timeout=300  
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Storage upload failed: {response.text}")

def save_metadata(image_data):
    """Save image metadata via Metadata Service"""
    response = requests.post(
        f"{METADATA_SERVICE_URL}/images",
        json=image_data,
        timeout=30
    )
    
    if response.status_code in [201, 409]: 
        return response.json()
    else:
        raise Exception(f"Metadata save failed: {response.text}")

def update_job_status(job_id, processed=0, failed=0, imported=None):
    """Update job status in Import Service"""
    try:
        requests.post(
            f"{IMPORT_SERVICE_URL}/import/update-status",
            json={
                'job_id': job_id,
                'processed': processed,
                'failed': failed,
                'imported': imported or []
            },
            timeout=10
        )
    except Exception as e:
        print(f"Error updating job status: {str(e)}")

def process_single_image(file_data, job_id):
    """Process a single image: download, upload to storage, save metadata"""
    try:
        # Download from Google Drive
        file_buffer = download_from_google_drive(file_data['id'])
        
        # Upload to cloud storage
        storage_result = upload_to_storage(
            file_buffer,
            file_data['name'],
            file_data['mimeType']
        )
        
        # Save metadata
        metadata = {
            'name': file_data['name'],
            'google_drive_id': file_data['id'],
            'size': int(file_data.get('size', 0)),
            'mime_type': file_data['mimeType'],
            'storage_path': storage_result['url'],
            'storage_provider': storage_result['provider']
        }
        
        saved_metadata = save_metadata(metadata)
        
        update_job_status(job_id, processed=1, imported=[saved_metadata])
        
        return {'success': True, 'image': saved_metadata}
        
    except Exception as e:
        print(f"Failed to process {file_data['name']}: {str(e)}")
        update_job_status(job_id, failed=1)
        return {'success': False, 'error': str(e), 'file': file_data['name']}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'worker-service'}), 200

@app.route('/process-batch', methods=['POST'])
def process_batch():
    """
    Process a batch of images concurrently
    This endpoint handles async processing with retry logic
    """
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        files = data.get('files', [])
        
        if not files:
            return jsonify({'error': 'No files to process'}), 400
        
        
        futures = []
        for file_data in files:
            future = executor.submit(process_single_image, file_data, job_id)
            futures.append(future)
        
        
        return jsonify({
            'message': f'Processing {len(files)} images',
            'job_id': job_id,
            'batch_size': len(files)
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process-single', methods=['POST'])
def process_single():
    """Process a single image (for retry or individual processing)"""
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        file_data = data.get('file_data')
        
        result = process_single_image(file_data, job_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5004))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
