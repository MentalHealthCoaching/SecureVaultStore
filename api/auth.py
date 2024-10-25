from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from secure_vault.core.crypto import CryptoSystem
from secure_vault.models.schemas import UserAuth, UserResponse
from secure_vault.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import jwt

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
crypto = CryptoSystem()

@router.post("/auth", response_model=dict)
async def authenticate(
    auth_data: UserAuth,
    db: AsyncSession = Depends(get_db)
):
    # Get or create user
    user = await db.get(auth_data.user_id)
    
    if not user:
        # Create new user
        keys = crypto.generate_user_keys(auth_data.password)
        user = User(
            user_id=auth_data.user_id,
            password_hash=crypto.hash_password(auth_data.password),
            master_key_encrypted=keys['master_key_encrypted'],
            public_key=keys['public_key'],
            created_at=datetime.utcnow()
        )
        db.add(user)
        await db.commit()
        is_new = True
    else:
        # Verify existing user
        if not crypto.verify_password(auth_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        is_new = False
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate token
    token = crypto.create_access_token(user.user_id)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "new_user": is_new
    }

@router.get("/users/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    
    try:
        payload = jwt.decode(token, crypto.jwt_secret, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
        
    user = await db.get(user_id)
    if user is None:
        raise credentials_exception
        
    return user
