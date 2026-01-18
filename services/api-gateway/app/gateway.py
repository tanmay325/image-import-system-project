from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

cors_origins = os.getenv('CORS_ORIGINS', '*').strip()
if cors_origins == '*' or cors_origins == '':
    CORS(app)
else:
    origins = [o.strip() for o in cors_origins.split(',') if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}})

# Service URLs
IMPORT_SERVICE_URL = os.getenv('IMPORT_SERVICE_URL', 'http://import-service:5001')
METADATA_SERVICE_URL = os.getenv('METADATA_SERVICE_URL', 'http://metadata-service:5002')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'api-gateway'}), 200

@app.route('/api/import/google-drive', methods=['POST'])
def import_from_google_drive():
    """Route import request to Import Service"""
    try:
        response = requests.post(
            f"{IMPORT_SERVICE_URL}/import/google-drive",
            json=request.get_json(),
            timeout=300
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Import service unavailable: {str(e)}'}), 503

@app.route('/api/import/status/<job_id>', methods=['GET'])
def get_import_status(job_id):
    """Get import job status from Import Service"""
    try:
        response = requests.get(f"{IMPORT_SERVICE_URL}/import/status/{job_id}", timeout=30)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Import service unavailable: {str(e)}'}), 503

@app.route('/api/images', methods=['GET'])
def get_images():
    """Route request to Metadata Service"""
    try:
        params = request.args.to_dict()
        response = requests.get(f"{METADATA_SERVICE_URL}/images", params=params, timeout=30)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Metadata service unavailable: {str(e)}'}), 503

@app.route('/api/images/all', methods=['GET'])
def get_all_images():
    """Get all images from Metadata Service"""
    try:
        response = requests.get(f"{METADATA_SERVICE_URL}/images/all", timeout=30)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Metadata service unavailable: {str(e)}'}), 503

@app.route('/api/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    """Get specific image from Metadata Service"""
    try:
        response = requests.get(f"{METADATA_SERVICE_URL}/images/{image_id}", timeout=30)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Metadata service unavailable: {str(e)}'}), 503

@app.route('/api/images/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete image via Metadata Service"""
    try:
        response = requests.delete(f"{METADATA_SERVICE_URL}/images/{image_id}", timeout=30)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Metadata service unavailable: {str(e)}'}), 503

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics from Metadata Service"""
    try:
        response = requests.get(f"{METADATA_SERVICE_URL}/stats", timeout=30)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Metadata service unavailable: {str(e)}'}), 503

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
