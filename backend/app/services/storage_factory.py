from flask import current_app
from app.services.s3_storage_service import S3StorageService

class StorageFactory:
    """Factory class to get the appropriate storage service based on configuration"""
    
    @staticmethod
    def get_storage_service():
        provider = current_app.config.get('STORAGE_PROVIDER', 'aws').lower()
        
        if provider == 'aws':
            return S3StorageService()
        else:
            raise ValueError(f"Unsupported storage provider: {provider}")
