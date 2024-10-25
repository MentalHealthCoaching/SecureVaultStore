from sqlalchemy import Column, String, DateTime, LargeBinary, Boolean, ForeignKey, Integer, Text
from sqlalchemy.sql import func
from secure_vault.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(50), primary_key=True)
    password_hash = Column(String(256), nullable=False)
    master_key_encrypted = Column(LargeBinary, nullable=False)
    recovery_key_encrypted = Column(LargeBinary)
    recovery_salt = Column(String(64))
    public_key = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))

class Document(Base):
    __tablename__ = "documents"
    
    document_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(50), ForeignKey("users.user_id"))
    encrypted_name = Column(Text, nullable=False)  # Verschlüsselter Dokumentname
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_access = Column(DateTime(timezone=True))
    mime_type = Column(String(128))
    encrypted_content = Column(LargeBinary)
    encrypted_preview = Column(LargeBinary)
    encrypted_key = Column(LargeBinary)
    encrypted_path = Column(Text)
    metadata = Column(Text)
    file_size = Column(Integer)
    tags = Column(Text)

class DocumentTag(Base):
    __tablename__ = "document_tags"
    
    tag_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.document_id"))
    tag = Column(String(64))  # Einzelnes Tag
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_user = Column(String(50), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    group_id = Column(String(36))
    encrypted_content = Column(LargeBinary)
    encrypted_keys = Column(Text)  # JSON: {user_id: encrypted_key}

class DocumentShare(Base):
    __tablename__ = "document_shares"
    
    share_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.document_id"))
    user_id = Column(String(50), ForeignKey("users.user_id"))
    encrypted_key = Column(LargeBinary)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String(50))
    action = Column(String(50))
    document_id = Column(String(36))
    message_id = Column(String(36))
    success = Column(Boolean)
    details = Column(Text)  # Non-sensitive additional info
