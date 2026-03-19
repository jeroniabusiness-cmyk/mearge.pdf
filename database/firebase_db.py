from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from firebase_admin import firestore
from database.firebase_config import FirebaseConfig
from database.models import User, Operation, UserSession, OperationType, OperationStatus
from utils.logger import logger

class FirebaseDB:
    """Firebase database operations"""
    
    def __init__(self):
        self.db = FirebaseConfig.get_firestore()
        self.users_collection = self.db.collection('users')
        self.operations_collection = self.db.collection('operations')
        self.sessions_collection = self.db.collection('sessions')
    
    # ================== USER OPERATIONS ==================
    
    def create_or_update_user(self, user_id: int, username: Optional[str], 
                             first_name: str, last_name: Optional[str] = None) -> User:
        """Create or update user in database"""
        try:
            user_ref = self.users_collection.document(str(user_id))
            user_doc = user_ref.get()
            
            now = datetime.now()
            
            if user_doc.exists:
                # Update existing user
                user_ref.update({
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'last_active': now.isoformat()
                })
                logger.info(f"Updated user: {user_id}")
                
                # Get updated user
                user_data = user_ref.get().to_dict()
                return User.from_dict(user_data)
            else:
                # Create new user
                user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    created_at=now,
                    last_active=now,
                    total_operations=0
                )
                user_ref.set(user.to_dict())
                logger.info(f"Created new user: {user_id}")
                return user
                
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            raise
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user from database"""
        try:
            user_ref = self.users_collection.document(str(user_id))
            user_doc = user_ref.get()
            
            if user_doc.exists:
                return User.from_dict(user_doc.to_dict())
            return None
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def increment_user_operations(self, user_id: int):
        """Increment user's total operations count"""
        try:
            user_ref = self.users_collection.document(str(user_id))
            user_ref.update({
                'total_operations': firestore.Increment(1),
                'last_active': datetime.now().isoformat()
            })
            logger.info(f"Incremented operations for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error incrementing user operations: {e}")
    
    def get_all_users_count(self) -> int:
        """Get total number of users"""
        try:
            users = self.users_collection.stream()
            return len(list(users))
        except Exception as e:
            logger.error(f"Error getting users count: {e}")
            return 0
    
    # ================== OPERATION OPERATIONS ==================
    
    def create_operation(self, user_id: int, operation_type: str, 
                        file_count: int = 0, input_size_bytes: int = 0) -> Operation:
        """Create new operation record"""
        try:
            operation_id = str(uuid.uuid4())
            
            operation = Operation(
                operation_id=operation_id,
                user_id=user_id,
                operation_type=operation_type,
                status=OperationStatus.PENDING.value,
                created_at=datetime.now(),
                file_count=file_count,
                input_size_bytes=input_size_bytes
            )
            
            self.operations_collection.document(operation_id).set(operation.to_dict())
            logger.info(f"Created operation: {operation_id} for user: {user_id}")
            
            return operation
            
        except Exception as e:
            logger.error(f"Error creating operation: {e}")
            raise
    
    def update_operation_status(self, operation_id: str, status: str, 
                               error_message: Optional[str] = None,
                               output_size_bytes: int = 0):
        """Update operation status"""
        try:
            operation_ref = self.operations_collection.document(operation_id)
            
            update_data = {
                'status': status,
            }
            
            if status in [OperationStatus.COMPLETED.value, OperationStatus.FAILED.value]:
                update_data['completed_at'] = datetime.now().isoformat()
            
            if error_message:
                update_data['error_message'] = error_message
            
            if output_size_bytes > 0:
                update_data['output_size_bytes'] = output_size_bytes
            
            operation_ref.update(update_data)
            logger.info(f"Updated operation {operation_id} status to: {status}")
            
        except Exception as e:
            logger.error(f"Error updating operation status: {e}")
    
    def get_user_operations(self, user_id: int, limit: int = 10) -> List[Operation]:
        """Get user's recent operations"""
        try:
            operations_query = (
                self.operations_collection
                .where('user_id', '==', user_id)
                .order_by('created_at', direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            operations = []
            for doc in operations_query.stream():
                operations.append(Operation.from_dict(doc.to_dict()))
            
            return operations
            
        except Exception as e:
            logger.error(f"Error getting user operations: {e}")
            return []
    
    def get_operations_count_by_type(self, operation_type: str) -> int:
        """Get count of operations by type"""
        try:
            operations = self.operations_collection.where('operation_type', '==', operation_type).stream()
            return len(list(operations))
        except Exception as e:
            logger.error(f"Error getting operations count: {e}")
            return 0
    
    # ================== SESSION OPERATIONS ==================
    
    def create_or_update_session(self, user_id: int, operation_type: Optional[str] = None) -> UserSession:
        """Create or update user session"""
        try:
            session_ref = self.sessions_collection.document(str(user_id))
            session_doc = session_ref.get()
            
            now = datetime.now()
            
            if session_doc.exists:
                # Update existing session
                session_ref.update({
                    'operation_type': operation_type,
                    'last_updated': now.isoformat()
                })
                session_data = session_ref.get().to_dict()
                return UserSession.from_dict(session_data)
            else:
                # Create new session
                session = UserSession(
                    user_id=user_id,
                    operation_type=operation_type,
                    created_at=now,
                    last_updated=now
                )
                session_ref.set(session.to_dict())
                return session
                
        except Exception as e:
            logger.error(f"Error creating/updating session: {e}")
            raise
    
    def get_session(self, user_id: int) -> Optional[UserSession]:
        """Get user session"""
        try:
            session_ref = self.sessions_collection.document(str(user_id))
            session_doc = session_ref.get()
            
            if session_doc.exists:
                return UserSession.from_dict(session_doc.to_dict())
            return None
            
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def add_file_to_session(self, user_id: int, file_info: Dict[str, Any]):
        """Add file to user session"""
        try:
            session_ref = self.sessions_collection.document(str(user_id))
            session_doc = session_ref.get()
            
            if session_doc.exists:
                session_data = session_doc.to_dict()
                files = session_data.get('files', [])
                files.append(file_info)
                
                session_ref.update({
                    'files': files,
                    'last_updated': datetime.now().isoformat()
                })
                logger.info(f"Added file to session for user: {user_id}")
            else:
                logger.warning(f"Session not found for user: {user_id}")
                
        except Exception as e:
            logger.error(f"Error adding file to session: {e}")
    
    def clear_session(self, user_id: int):
        """Clear user session"""
        try:
            session_ref = self.sessions_collection.document(str(user_id))
            session_ref.delete()
            logger.info(f"Cleared session for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
    
    # ================== STATISTICS ==================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        try:
            total_users = self.get_all_users_count()
            
            # Get operations count
            operations = list(self.operations_collection.stream())
            total_operations = len(operations)
            
            # Count by type
            merge_count = sum(1 for op in operations if op.to_dict().get('operation_type') == OperationType.MERGE_PDF.value)
            img2pdf_count = sum(1 for op in operations if op.to_dict().get('operation_type') == OperationType.IMAGE_TO_PDF.value)
            
            # Count by status
            completed_count = sum(1 for op in operations if op.to_dict().get('status') == OperationStatus.COMPLETED.value)
            failed_count = sum(1 for op in operations if op.to_dict().get('status') == OperationStatus.FAILED.value)
            
            return {
                'total_users': total_users,
                'total_operations': total_operations,
                'operations_by_type': {
                    'merge_pdf': merge_count,
                    'image_to_pdf': img2pdf_count
                },
                'operations_by_status': {
                    'completed': completed_count,
                    'failed': failed_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

# Global database instance
firebase_db = FirebaseDB()
