import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
 
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
            SQLALCHEMY_DATABASE_URI = (
                f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
            )
        elif engine == 'mssql':
            # SQL Server connection string with pyodbc
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
            SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"
        else:
            raise ValueError(f"Unsupported DB_ENGINE: {engine}")
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///images.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Cloud Storage Configuration
    STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 'aws')  # aws
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
    
    # Google Drive API
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  
