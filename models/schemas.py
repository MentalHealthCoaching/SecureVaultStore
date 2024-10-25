from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class UserAuth(BaseModel):
    user_id: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    created_at: datetime
    last_login: Optional[datetime]

class DocumentCreate(BaseModel):
    recipients: Optional[List[str]] = []

class DocumentResponse(BaseModel):
    document_id: str
    owner_id: str
    created_at: datetime
    modified_at: datetime
    last_access: Optional[datetime]
    mime_type: str
    file_size: int
    encrypted_preview: Optional[str]

class MessageCreate(BaseModel):
    content: str
    recipients: List[str]
    group_id: Optional[str]

class MessageResponse(BaseModel):
    message_id: str
    from_user: str
    created_at: datetime
    group_id: Optional[str]
    encrypted_content: str

class DocumentDelete(BaseModel):
    password: str

class AuditLogResponse(BaseModel):
    log_id: str
    timestamp: datetime
    user_id: str
    action: str
    success: bool
    details: Optional[str]
