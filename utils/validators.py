import os
from typing import Tuple
from config.settings import Settings
from utils.logger import logger

class FileValidator:
    """Validate uploaded files"""
    
    @staticmethod
    def validate_pdf(filename: str, file_size: int) -> Tuple[bool, str]:
        """Validate PDF file"""
        
        # Check extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in Settings.ALLOWED_PDF_EXTENSIONS:
            return False, f"❌ Invalid file type. Only PDF files are allowed.\nReceived: {ext}"
        
        # Check size
        if file_size > Settings.MAX_FILE_SIZE_BYTES:
            max_size_mb = Settings.MAX_FILE_SIZE_MB
            actual_size_mb = file_size / (1024 * 1024)
            return False, f"❌ File too large!\nMaximum: {max_size_mb}MB\nYour file: {actual_size_mb:.2f}MB"
        
        return True, "✅ Valid PDF file"
    
    @staticmethod
    def validate_image(filename: str, file_size: int) -> Tuple[bool, str]:
        """Validate image file"""
        
        # Check extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in Settings.ALLOWED_IMAGE_EXTENSIONS:
            allowed = ', '.join(Settings.ALLOWED_IMAGE_EXTENSIONS)
            return False, f"❌ Invalid image type.\n\nAllowed formats:\n{allowed}\n\nReceived: {ext}"
        
        # Check size
        if file_size > Settings.MAX_FILE_SIZE_BYTES:
            max_size_mb = Settings.MAX_FILE_SIZE_MB
            actual_size_mb = file_size / (1024 * 1024)
            return False, f"❌ File too large!\nMaximum: {max_size_mb}MB\nYour file: {actual_size_mb:.2f}MB"
        
        return True, "✅ Valid image file"
    
    @staticmethod
    def validate_session_file_count(current_count: int) -> Tuple[bool, str]:
        """Validate if more files can be added to session"""
        if current_count >= Settings.MAX_FILES_PER_SESSION:
            return False, f"❌ Maximum files limit reached!\nLimit: {Settings.MAX_FILES_PER_SESSION} files per session"
        
        return True, "✅ Can add more files"
