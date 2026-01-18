from flask import Blueprint, request, jsonify
from app.models.image import Image
from app import db

image_bp = Blueprint('images', __name__)

@image_bp.route('/images', methods=['GET'])
def get_images():
    """Get all imported images with metadata"""
    try:
        # Get query parameters for filtering/pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        storage_provider = request.args.get('storage_provider', None)
        
        # Build query
        query = Image.query
        
        if storage_provider:
            query = query.filter_by(storage_provider=storage_provider)
        
        # Order by most recent first
        query = query.order_by(Image.created_at.desc())
        
        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        images = [image.to_dict() for image in pagination.items]
        
        return jsonify({
            'images': images,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_bp.route('/images/all', methods=['GET'])
def get_all_images():
    """Get ALL database entries without pagination"""
    try:
        # Get all images from database
        images = Image.query.order_by(Image.created_at.desc()).all()
        
        # Convert to dictionary format
        images_list = [image.to_dict() for image in images]
        
        return jsonify({
            'success': True,
            'total': len(images_list),
            'images': images_list
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@image_bp.route('/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    """Get a specific image by ID"""
    try:
        image = Image.query.get(image_id)
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        return jsonify(image.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_bp.route('/images/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete an image"""
    try:
        image = Image.query.get(image_id)
        
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        # Delete from cloud storage
        from app.services.storage_factory import StorageFactory
        storage_service = StorageFactory.get_storage_service()
        storage_service.delete_file(image.storage_path)
        
        # Delete from database
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'message': 'Image deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@image_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics about imported images"""
    try:
        total_images = Image.query.count()
        total_size = db.session.query(db.func.sum(Image.size)).scalar() or 0
        
        # Count by storage provider
        aws_count = Image.query.filter_by(storage_provider='aws').count()
        
        return jsonify({
            'total_images': total_images,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'aws_images': aws_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
