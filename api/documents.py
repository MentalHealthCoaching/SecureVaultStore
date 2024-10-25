from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Header
from fastapi.responses import StreamingResponse
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime
import uuid
import os
import io

from secure_vault.core.database import get_db
from secure_vault.core.crypto import CryptoSystem
from secure_vault.models.models import Document, User, AuditLog
from secure_vault.api.auth import get_current_user, get_optional_user
from secure_vault.core.config import get_settings

router = APIRouter()
settings = get_settings()
crypto = CryptoSystem()

@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),                    # Klartext Name
    recipient_id: str = Form(...),            # User ID des Empfängers
    mime_type: Optional[str] = Form(None),    # Optional, wird automatisch erkannt
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_optional_user)  # Optional authentifiziert
):
    try:
        # Prüfe Dateigröße
        content = await file.read()
        if len(content) > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB"
            )

        # Hole Empfänger-Public-Key
        recipient = await db.execute(
            select(User).where(User.user_id == recipient_id)
        )
        recipient = recipient.scalar_one_or_none()
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient not found")

        # Generiere Document Key und verschlüssele Dokument
        document_key = os.urandom(32)
        encrypted_content = crypto.encrypt_with_key(content, document_key)
        encrypted_name = crypto.encrypt_with_key(name.encode(), document_key)
        
        # Verschlüssele Document Key mit Public Key des Empfängers
        encrypted_key = crypto.encrypt_key_for_recipient(
            document_key,
            recipient.public_key
        )
        
        # Erstelle Preview falls möglich
        encrypted_preview = None
        if file.content_type.startswith('image/'):
            preview = await create_preview(content)
            encrypted_preview = crypto.encrypt_with_key(preview, document_key)

        # Speichere Dokument
        document = Document(
            document_id=str(uuid.uuid4()),
            owner_id=current_user.user_id if current_user else None,
            recipient_id=recipient_id,
            encrypted_name=encrypted_name,
            mime_type=mime_type or file.content_type,
            encrypted_content=encrypted_content,
            encrypted_key=encrypted_key,
            encrypted_preview=encrypted_preview,
            file_size=len(content),
            created_at=datetime.utcnow()
        )
        
        db.add(document)
        
        # Audit Log
        log = AuditLog(
            action="upload_document",
            document_id=document.document_id,
            success=True,
            details=f"Uploaded for recipient: {recipient_id}"
        )
        if current_user:
            log.user_id = current_user.user_id
            
        db.add(log)
        
        await db.commit()
        
        return {
            "document_id": document.document_id,
            "recipient_id": recipient_id,
            "created_at": document.created_at,
            "status": "delivered"
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents(
    path_prefix: Optional[str] = None,
    tags: Optional[str] = None,
    mime_type: Optional[str] = None,
    received_only: Optional[bool] = False,
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Liste Dokumente mit optionaler Filterung"""
    query = select(Document)

    # Filter für empfangene oder eigene Dokumente
    if received_only:
        query = query.where(Document.recipient_id == current_user.user_id)
    else:
        query = query.where(
            or_(
                Document.recipient_id == current_user.user_id,
                Document.owner_id == current_user.user_id
            )
        )

    # Weitere Filter
    if mime_type:
        query = query.where(Document.mime_type == mime_type)
    if tags:
        tag_list = tags.split(',')
        query = query.where(Document.tags.contains(tag_list))

    # Pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Log access
    log = AuditLog(
        user_id=current_user.user_id,
        action="list_documents",
        success=True
    )
    db.add(log)
    await db.commit()

    return {
        "documents": documents,
        "page": page,
        "per_page": per_page,
        "total": len(documents)
    }

@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Hole ein spezifisches Dokument"""
    document = await db.execute(
        select(Document).where(
            and_(
                Document.document_id == document_id,
                or_(
                    Document.recipient_id == current_user.user_id,
                    Document.owner_id == current_user.user_id
                )
            )
        )
    )
    document = document.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update last access
    document.last_access = datetime.utcnow()
    
    # Log access
    log = AuditLog(
        user_id=current_user.user_id,
        action="access_document",
        document_id=document_id,
        success=True
    )
    db.add(log)
    
    await db.commit()

    return document

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    password: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Lösche ein Dokument (nur als Besitzer möglich)"""
    # Prüfe ob Dokument existiert und User der Besitzer ist
    document = await db.execute(
        select(Document).where(
            and_(
                Document.document_id == document_id,
                Document.owner_id == current_user.user_id
            )
        )
    )
    document = document.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verifiziere Passwort
    if not crypto.verify_password(password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Lösche Dokument
    await db.delete(document)
    
    # Log deletion
    log = AuditLog(
        user_id=current_user.user_id,
        action="delete_document",
        document_id=document_id,
        success=True
    )
    db.add(log)
    
    await db.commit()
    
    return {"status": "success"}

async def create_preview(content: bytes, max_size: tuple = (100, 100)) -> bytes:
    """Erstelle eine Vorschau für Bilder"""
    image = Image.open(io.BytesIO(content))
    image.thumbnail(max_size)
    preview_bytes = io.BytesIO()
    image.save(preview_bytes, format='PNG')
    return preview_bytes.getvalue()

