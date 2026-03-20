import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Firebase Configuration
    if os.getenv('RENDER'):
        FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', '/etc/secrets/firebase_credentials.json')
    else:
        FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', './config/firebase-credentials.json')
    
    # File Configuration
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 50))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    TEMP_FOLDER = os.getenv('TEMP_FOLDER', './temp')
    LOG_FOLDER = os.getenv('LOG_FOLDER', './logs')
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', 30))
    MAX_FILES_PER_SESSION = int(os.getenv('MAX_FILES_PER_SESSION', 20))
    
    # Admin Configuration
    ADMIN_USER_IDS_STR = os.getenv('ADMIN_USER_IDS', '')
    ADMIN_USER_IDS: List[int] = []
    
    if ADMIN_USER_IDS_STR:
        try:
            ADMIN_USER_IDS = [int(uid.strip()) for uid in ADMIN_USER_IDS_STR.split(',') if uid.strip()]
        except ValueError:
            ADMIN_USER_IDS = []
    
    # Allowed file formats
    ALLOWED_PDF_EXTENSIONS = ['.pdf']
    ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']
    
    # Supported conversion formats
    SUPPORTED_CONVERSIONS = {
        'pdf_to_image': ['jpg', 'png'],
        'pdf_to_doc': ['docx'],
        'pdf_to_text': ['txt']
    }
    
    @staticmethod
    def validate():
        """Validate required settings"""
        if not Settings.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN not found in environment variables")
        
        if not os.path.exists(Settings.FIREBASE_CREDENTIALS_PATH):
            raise ValueError(f"❌ Firebase credentials not found at: {Settings.FIREBASE_CREDENTIALS_PATH}")
        
        # Create necessary folders
        os.makedirs(Settings.TEMP_FOLDER, exist_ok=True)
        os.makedirs(Settings.LOG_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(Settings.FIREBASE_CREDENTIALS_PATH), exist_ok=True)
        
        print("✅ Settings validated successfully")

# Validate settings on import
Settings.validate()
