import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from config.settings import Settings
from utils.logger import logger

class FileManager:
    """Manage temporary files for the bot"""
    
    @staticmethod
    def get_user_folder(user_id: int) -> str:
        """Get or create user-specific temp folder"""
        user_folder = os.path.join(Settings.TEMP_FOLDER, str(user_id))
        os.makedirs(user_folder, exist_ok=True)
        return user_folder
    
    @staticmethod
    def generate_unique_filename(extension: str, prefix: str = "") -> str:
        """Generate unique filename with timestamp and UUID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        if prefix:
            return f"{prefix}_{timestamp}_{unique_id}{extension}"
        return f"{timestamp}_{unique_id}{extension}"
    
    @staticmethod
    def save_file(user_id: int, file_data: bytes, extension: str, prefix: str = "") -> str:
        """Save file to user's temp folder"""
        try:
            user_folder = FileManager.get_user_folder(user_id)
            filename = FileManager.generate_unique_filename(extension, prefix)
            filepath = os.path.join(user_folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Saved file: {filepath} ({len(file_data)} bytes)")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(filepath)
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return 0
    
    @staticmethod
    def file_exists(filepath: str) -> bool:
        """Check if file exists"""
        return os.path.isfile(filepath)
    
    @staticmethod
    def cleanup_user_files(user_id: int):
        """Clean up all files for a specific user"""
        user_folder = FileManager.get_user_folder(user_id)
        
        try:
            deleted_count = 0
            for filename in os.listdir(user_folder):
                filepath = os.path.join(user_folder, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    deleted_count += 1
            
            # Remove folder if empty
            if not os.listdir(user_folder):
                os.rmdir(user_folder)
                logger.info(f"Deleted empty user folder: {user_folder}")
            
            logger.info(f"Cleaned up {deleted_count} files for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up user files: {e}")
    
    @staticmethod
    def cleanup_old_files(hours: int = 24):
        """Clean up files older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            total_deleted = 0
            
            for user_folder in os.listdir(Settings.TEMP_FOLDER):
                folder_path = os.path.join(Settings.TEMP_FOLDER, user_folder)
                
                if not os.path.isdir(folder_path):
                    continue
                
                for filename in os.listdir(folder_path):
                    filepath = os.path.join(folder_path, filename)
                    
                    if os.path.isfile(filepath):
                        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                        
                        if file_time < cutoff_time:
                            os.remove(filepath)
                            total_deleted += 1
                
                # Remove empty folders
                if not os.listdir(folder_path):
                    os.rmdir(folder_path)
            
            logger.info(f"Cleanup completed: Deleted {total_deleted} old files")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension from filename"""
        return os.path.splitext(filename)[1].lower()
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
