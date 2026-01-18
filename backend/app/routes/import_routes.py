from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.image import Image
from app.services.google_drive_service import GoogleDriveService
from app.services.storage_factory import StorageFactory
import logging

import_bp = Blueprint('import', __name__)
logger = logging.getLogger(__name__)

@import_bp.route('/import/google-drive', methods=['POST'])
def import_from_google_drive():
    """Import images from a public Google Drive folder"""
    try:
        data = request.get_json()
        
        if not data or 'folder_url' not in data:
            return jsonify({'error': 'folder_url is required'}), 400
        
        folder_url = data['folder_url']
        
        # Extract folder ID
        drive_service = GoogleDriveService()
        folder_id = drive_service.extract_folder_id(folder_url)
        
        # Get list of images from Google Drive
        files = drive_service.list_images_in_folder(folder_id)
        
        if not files:
            return jsonify({'message': 'No images found in the folder'}), 200
        
        # Get storage service (AWS S3)
        storage_service = StorageFactory.get_storage_service()
        
        imported_images = []
        failed_imports = []
        
        for file in files:
            try:
                # Check if already imported
                existing_image = Image.query.filter_by(google_drive_id=file['id']).first()
                if existing_image:
                    logger.info(f"Image {file['name']} already imported, skipping")
                    continue
                
                # Download file from Google Drive
                file_buffer = drive_service.download_file(file['id'])
                
                # Upload to cloud storage
                storage_path = storage_service.upload_file(
                    file_buffer,
                    file['name'],
                    file['mimeType']
                )
                
                # Save metadata to database
                image = Image(
                    name=file['name'],
                    google_drive_id=file['id'],
                    size=int(file.get('size', 0)),
                    mime_type=file['mimeType'],
                    storage_path=storage_path,
                    storage_provider=current_app.config.get('STORAGE_PROVIDER', 'aws')
                )
                
                db.session.add(image)
                db.session.commit()
                
                imported_images.append(image.to_dict())
                logger.info(f"Successfully imported {file['name']}")
                
            except Exception as e:
                logger.error(f"Failed to import {file['name']}: {str(e)}")
                failed_imports.append({
                    'name': file['name'],
                    'error': str(e)
                })
                continue
        
        return jsonify({
            'message': f'Import completed. {len(imported_images)} images imported successfully',
            'imported': imported_images,
            'failed': failed_imports,
            'total_found': len(files)
        }), 200
        
    except Exception as e:
        logger.error(f"Import error: {str(e)}")
        return jsonify({'error': str(e)}), 500
