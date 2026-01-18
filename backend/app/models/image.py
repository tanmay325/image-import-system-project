from app import db
from datetime import datetime

class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    google_drive_id = db.Column(db.String(255), unique=True, nullable=False)
    size = db.Column(db.BigInteger, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    storage_provider = db.Column(db.String(20), nullable=False)  # e.g. 'aws'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
