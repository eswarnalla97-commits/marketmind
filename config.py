import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'marketmind-dwdm-secret-key-2024')
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'marketmind_dw.db')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
    SAMPLE_DATA_PATH = os.path.join(DATA_DIR, 'sample_transactions.csv')
    SAMPLE_TEMPLATE_PATH = os.path.join(DATA_DIR, 'sample_template.csv')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'csv'}

config = Config()
