from flask import Flask, request, jsonify
from flask_cors import CORS
from celery import Celery
import os
import requests
import uuid
import json
from dotenv import load_dotenv
from googleapiclient.discovery import build
import re

load_dotenv()

app = Flask(__name__)
CORS(app)


app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://redis:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL', 'redis://redis:6379/0')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

WORKER_SERVICE_URL = os.getenv('WORKER_SERVICE_URL', 'http://worker-service:5004')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')


job_statuses = {}

def extract_folder_id(folder_url):
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

def list_images_in_folder(folder_id):
    """List all images in a Google Drive folder"""
    try:
        service = build('drive', 'v3', developerKey=GOOGLE_API_KEY)
        query = f"'{folder_id}' in parents and (mimeType contains 'image/')"
        
        results = service.files().list(
            q=query,
            pageSize=1000,  # Handle large folders
            fields="files(id, name, size, mimeType)"
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        raise Exception(f"Error fetching files from Google Drive: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'import-service'}), 200

@app.route('/import/google-drive', methods=['POST'])
def import_from_google_drive():
    """
    Initiate async import from Google Drive
    Returns job_id for status tracking
    """
    try:
        data = request.get_json()
        
        if not data or 'folder_url' not in data:
            return jsonify({'error': 'folder_url is required'}), 400
        
        folder_url = data['folder_url']
        folder_id = extract_folder_id(folder_url)
        
        # List images from Google Drive
        files = list_images_in_folder(folder_id)
        
        if not files:
            return jsonify({'message': 'No images found in the folder'}), 200
        
        
        job_id = str(uuid.uuid4())
        
        
        job_statuses[job_id] = {
            'status': 'processing',
            'total': len(files),
            'processed': 0,
            'failed': 0,
            'imported': []
        }
        
        # Send files to worker service for async processing
        batch_size = 100  
        for i in range(0, len(files), batch_size):
            batch = files[i:i+batch_size]
            
            try:
                requests.post(
                    f"{WORKER_SERVICE_URL}/process-batch",
                    json={
                        'job_id': job_id,
                        'files': batch
                    },
                    timeout=5  
                )
            except Exception as e:
                print(f"Error sending batch to worker: {str(e)}")
        
        return jsonify({
            'job_id': job_id,
            'message': f'Import job started for {len(files)} images',
            'total_images': len(files)
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/import/status/<job_id>', methods=['GET'])
def get_import_status(job_id):
    """Get status of import job"""
    if job_id not in job_statuses:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job_statuses[job_id]), 200

@app.route('/import/update-status', methods=['POST'])
def update_job_status():
    """Update job status (called by worker service)"""
    data = request.get_json()
    job_id = data.get('job_id')
    
    if job_id in job_statuses:
        if 'processed' in data:
            job_statuses[job_id]['processed'] += data['processed']
        if 'failed' in data:
            job_statuses[job_id]['failed'] += data['failed']
        if 'imported' in data:
            job_statuses[job_id]['imported'].extend(data['imported'])
        
        
        total = job_statuses[job_id]['total']
        processed = job_statuses[job_id]['processed']
        failed = job_statuses[job_id]['failed']
        
        if processed + failed >= total:
            job_statuses[job_id]['status'] = 'completed'
    
    return jsonify({'success': True}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
