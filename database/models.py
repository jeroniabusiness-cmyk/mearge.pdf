from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

class OperationType(Enum):
    """Types of operations"""
    MERGE_PDF = "merge_pdf"
    IMAGE_TO_PDF = "image_to_pdf"
    PDF_TO_IMAGE = "pdf_to_image"
    PDF_TO_DOCX = "pdf_to_docx"
    PDF_TO_TXT = "pdf_to_txt"

class OperationStatus(Enum):
    """Status of operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class User:
    """User model"""
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    created_at: datetime
    last_active: datetime
    total_operations: int = 0
    is_blocked: bool = False
    is_premium: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_active'] = self.last_active.isoformat()
        return data
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'User':
        """Create User from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_active'] = datetime.fromisoformat(data['last_active'])
        return User(**data)

@dataclass
class Operation:
    """Operation model"""
    operation_id: str
    user_id: int
    operation_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_count: int = 0
    input_size_bytes: int = 0
    output_size_bytes: int = 0
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Operation':
        """Create Operation from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return Operation(**data)

@dataclass
class UserSession:
    """User session model for managing temporary data"""
    user_id: int
    operation_type: Optional[str] = None
    files: List[Dict[str, Any]] = None
    created_at: datetime = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.files is None:
            self.files = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'operation_type': self.operation_type,
            'files': self.files,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'UserSession':
        """Create UserSession from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return UserSession(**data)
