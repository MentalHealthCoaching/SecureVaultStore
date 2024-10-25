from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_type: str = "sqlite"
    database_host: Optional[str] = None
    database_port: Optional[int] = None
    database_name: str = "secure_vault.db"
    database_user: Optional[str] = None
    database_password: Optional[str] = None
    
    # Storage
    max_file_size_mb: int = 50
    temp_dir: str = "/tmp/secure_vault"
    data_dir: str = "/var/secure_vault/data"
    
    # Security
    jwt_secret: str = "your-secret-key-change-in-production"
    token_validity_hours: int = 24
    min_password_length: int = 12
    crypto_iterations: int = 480000
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_workers: int = 4
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings() -> Settings:
    return Settings()
