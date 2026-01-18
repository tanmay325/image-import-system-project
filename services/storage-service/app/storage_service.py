from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
import base64
import io

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 'aws')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

class StorageService:
    @staticmethod
    def _s3_client():
        
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            return boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
        return boto3.client('s3', region_name=AWS_REGION)

    @staticmethod
    def upload_to_s3(file_buffer, filename, mime_type):
        """Upload file to AWS S3"""
        try:
            s3_client = StorageService._s3_client()
            
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            s3_client.upload_fileobj(
                file_buffer,
                AWS_BUCKET_NAME,
                unique_filename,
                ExtraArgs={'ContentType': mime_type, 'ACL': 'public-read'}
            )
            
            url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
            return {'success': True, 'url': url, 'provider': 'aws'}
        except ClientError as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_from_s3(file_path):
        """Delete file from AWS S3"""
        try:
            s3_client = StorageService._s3_client()
            
            filename = file_path.split('/')[-1]
            s3_client.delete_object(Bucket=AWS_BUCKET_NAME, Key=filename)
            return {'success': True}
        except ClientError as e:
            return {'success': False, 'error': str(e)}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'storage-service'}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload file to configured cloud storage"""
    try:
        data = request.get_json()
        file_data_base64 = data.get('file_data')
        filename = data.get('filename')
        mime_type = data.get('mime_type')
        provider = data.get('provider', STORAGE_PROVIDER)
        
        
        file_bytes = base64.b64decode(file_data_base64)
        file_buffer = io.BytesIO(file_bytes)
        
        if provider != 'aws':
            return jsonify({'error': 'Invalid storage provider'}), 400

        result = StorageService.upload_to_s3(file_buffer, filename, mime_type)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete', methods=['POST'])
def delete_file():
    """Delete file from cloud storage"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        provider = data.get('provider', STORAGE_PROVIDER)
        
        if provider != 'aws':
            return jsonify({'error': 'Invalid storage provider'}), 400

        result = StorageService.delete_from_s3(file_path)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=False)
