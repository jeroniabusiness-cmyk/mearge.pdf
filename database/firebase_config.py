import firebase_admin
from firebase_admin import credentials, firestore
from config.settings import Settings
from utils.logger import logger
import os

class FirebaseConfig:
    """Firebase configuration and initialization"""
    
    _initialized = False
    _firestore_client = None
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK (Firestore only)"""
        if cls._initialized:
            logger.info("Firebase already initialized")
            return
        
        try:
            # Check if credentials file exists
            if not os.path.exists(Settings.FIREBASE_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Firebase credentials file not found: {Settings.FIREBASE_CREDENTIALS_PATH}"
                )
            
            # Initialize Firebase Admin (no databaseURL = no grpcio dependency)
            cred = credentials.Certificate(Settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            
            cls._initialized = True
            logger.info("✅ Firebase initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase: {e}")
            raise
    
    @classmethod
    def get_firestore(cls):
        """Get Firestore client"""
        if not cls._initialized:
            cls.initialize()
        
        if cls._firestore_client is None:
            cls._firestore_client = firestore.client()
        
        return cls._firestore_client

# Initialize on import
try:
    FirebaseConfig.initialize()
except Exception as e:
    logger.error(f"Failed to initialize Firebase on import: {e}")
