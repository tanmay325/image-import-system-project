from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

app = Flask(__name__)
CORS(app)


# mysql (AWS RDS MySQL)
DB_ENGINE = os.getenv('DB_ENGINE', '').strip().lower() 
DB_SERVER = os.getenv('DB_SERVER')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server')

if all([DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD]):
    engine = DB_ENGINE or 'mysql'

    if engine == 'mysql':
        port = int(DB_PORT) if DB_PORT else 3306
        user = quote_plus(DB_USER)
        password = quote_plus(DB_PASSWORD)
        host = DB_SERVER
        dbname = DB_NAME
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
        )
    elif engine == 'mssql':
        connection_string = (
            f"DRIVER={{{DB_DRIVER}}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        params = quote_plus(connection_string)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
    else:
        raise ValueError(f"Unsupported DB_ENGINE: {engine}")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///images.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 20,  
    'max_overflow': 40
}

db = SQLAlchemy(app)

# Image Model
class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    google_drive_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    size = db.Column(db.BigInteger, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    storage_provider = db.Column(db.String(20), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'google_drive_id': self.google_drive_id,
            'size': self.size,
            'mime_type': self.mime_type,
            'storage_path': self.storage_path,
            'storage_provider': self.storage_provider,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Create tables
with app.app_context():
    db.create_all()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'metadata-service'}), 200

@app.route('/images', methods=['GET'])
def get_images():
    """Get paginated images"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        storage_provider = request.args.get('storage_provider', None)
        
        query = Image.query
        
        if storage_provider:
            query = query.filter_by(storage_provider=storage_provider)
        
        query = query.order_by(Image.created_at.desc())
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

@app.route('/images/all', methods=['GET'])
def get_all_images():
    """Get all images without pagination"""
    try:
        images = Image.query.order_by(Image.created_at.desc()).all()
        images_list = [image.to_dict() for image in images]
        
        return jsonify({
            'success': True,
            'total': len(images_list),
            'images': images_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    """Get specific image"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        return jsonify(image.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/images', methods=['POST'])
def create_image():
    """Create new image metadata (called by worker service)"""
    try:
        data = request.get_json()
        
    
        existing = Image.query.filter_by(google_drive_id=data['google_drive_id']).first()
        if existing:
            return jsonify({'error': 'Image already exists', 'image': existing.to_dict()}), 409
        
        image = Image(
            name=data['name'],
            google_drive_id=data['google_drive_id'],
            size=data['size'],
            mime_type=data['mime_type'],
            storage_path=data['storage_path'],
            storage_provider=data['storage_provider']
        )
        
        db.session.add(image)
        db.session.commit()
        
        return jsonify(image.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/images/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete image metadata"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'message': 'Image deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    try:
        total_images = Image.query.count()
        total_size = db.session.query(db.func.sum(Image.size)).scalar() or 0
        aws_count = Image.query.filter_by(storage_provider='aws').count()
        return jsonify({
            'total_images': total_images,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'aws_images': aws_count,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)
