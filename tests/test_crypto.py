import pytest
from secure_vault.core.crypto import CryptoSystem
import os

@pytest.fixture
def crypto_system():
    return CryptoSystem()

def test_password_hashing(crypto_system):
    password = "test_password123"
    password_hash = crypto_system.hash_password(password)
    
    assert crypto_system.verify_password(password, password_hash)
    assert not crypto_system.verify_password("wrong_password", password_hash)

def test_document_encryption(crypto_system):
    # Generiere Test-Keys
    password = "test_password123"
    user_keys = crypto_system.generate_user_keys(password)
    
    # Test-Dokument
    test_content = b"Hello, World!"
    
    # Verschlüssele
    encryption_result = crypto_system.encrypt_document(
        test_content,
        user_keys['public_key']
    )
    
    # Entschlüssele
    decrypted_content = crypto_system.decrypt_document(
        encryption_result['encrypted_content'],
        encryption_result['encrypted_key'],
        encryption_result['metadata'],
        user_keys['master_key_encrypted'],
        crypto_system._derive_key_from_password(
            password,
            user_keys['master_salt']
        )
    )
    
    assert decrypted_content == test_content

def test_preview_encryption(crypto_system):
    # Generiere Test-Keys
    user_keys = crypto_system.generate_user_keys("test_password123")
    
    # Test-Preview
    test_preview = b"Preview Data"
    
    # Verschlüssele Preview
    encrypted_preview = crypto_system.encrypt_preview(
        test_preview,
        user_keys['public_key']
    )
    
    assert encrypted_preview is not None
    assert len(encrypted_preview) > len(test_preview)
