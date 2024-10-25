from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from secure_vault.core.crypto import CryptoSystem
from secure_vault.models.schemas import MessageCreate, MessageResponse
from secure_vault.core.database import get_db
from secure_vault.models.models import Message, User, AuditLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json
import uuid

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
crypto = CryptoSystem()

@router.post("/messages", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    # Verschlüssele Nachricht
    message_key = crypto.generate_message_key()
    encrypted_content = crypto.encrypt_message(
        message_data.content.encode(),
        message_key
    )
    
    # Verschlüssele Nachrichtenschlüssel für jeden Empfänger
    encrypted_keys = {}
    for recipient_id in message_data.recipients:
        recipient = await db.execute(
            select(User).where(User.user_id == recipient_id)
        )
        recipient = recipient.scalar_one_or_none()
        if recipient:
            encrypted_key = crypto.encrypt_key_for_recipient(
                message_key,
                recipient.public_key
            )
            encrypted_keys[recipient_id] = encrypted_key.hex()
    
    # Füge Sender hinzu
    sender = await db.execute(
        select(User).where(User.user_id == current_user)
    )
    sender = sender.scalar_one_or_none()
    sender_key = crypto.encrypt_key_for_recipient(
        message_key,
        sender.public_key
    )
    encrypted_keys[current_user] = sender_key.hex()
    
    # Speichere Nachricht
    message = Message(
        message_id=str(uuid.uuid4()),
        from_user=current_user,
        group_id=message_data.group_id,
        encrypted_content=encrypted_content,
        encrypted_keys=json.dumps(encrypted_keys)
    )
    
    db.add(message)
    
    # Audit Log
    log = AuditLog(
        user_id=current_user,
        action="send_message",
        message_id=message.message_id,
        success=True,
        details=f"recipients: {len(message_data.recipients)}"
    )
    db.add(log)
    
    await db.commit()
    return message

@router.get("/messages", response_model=list[MessageResponse])
async def get_messages(
    current_user: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    # Hole alle Nachrichten wo der User Empfänger ist
    messages = await db.execute(
        select(Message).where(
            Message.encrypted_keys.like(f'%"{current_user}"%')
        ).order_by(Message.created_at.desc())
    )
    messages = messages.scalars().all()
    
    # Audit Log für Zugriff
    log = AuditLog(
        user_id=current_user,
        action="access_messages",
        success=True
    )
    db.add(log)
    
    await db.commit()
    return messages
