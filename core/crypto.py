from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asymmetric_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from secure_vault.core.config import get_settings
import base64
import os
import json
import jwt
from datetime import datetime, timedelta

class CryptoSystem:
    def __init__(self):
        self.settings = get_settings()
        self.jwt_secret = self.settings.jwt_secret.encode()
    
    def generate_user_keys(self, password: str) -> dict:
        """Generiert alle Schlüssel für einen neuen Benutzer"""
        # Generiere Master Salt
        master_salt = os.urandom(16)
        
        # Generiere Master Key aus Passwort
        master_key = self._derive_key_from_password(password, master_salt)
        
        # Generiere RSA Schlüsselpaar
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        public_key = private_key.public_key()
        
        # Verschlüssele Private Key mit Master Key
        f = Fernet(base64.urlsafe_b64encode(master_key))
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        encrypted_private_key = f.encrypt(private_pem)
        
        return {
            'master_salt': master_salt,
            'master_key_encrypted': encrypted_private_key,
            'public_key': public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        }

    def encrypt_document(self, content: bytes, public_key_pem: bytes) -> dict:
        """Verschlüsselt ein Dokument"""
        # Generiere Document Key
        document_key = os.urandom(32)
        
        # Verschlüssele Content mit AES-GCM
        nonce = os.urandom(12)
        cipher = Cipher(
            algorithms.AES(document_key),
            modes.GCM(nonce)
        )
        encryptor = cipher.encryptor()
        
        encrypted_content = encryptor.update(content) + encryptor.finalize()
        
        # Verschlüssele Document Key mit Public Key
        public_key = serialization.load_pem_public_key(public_key_pem)
        encrypted_key = public_key.encrypt(
            document_key,
            asymmetric_padding.OAEP(
                mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return {
            'encrypted_content': encrypted_content,
            'encrypted_key': encrypted_key,
            'document_key': document_key,
            'metadata': json.dumps({
                'nonce': base64.b64encode(nonce).decode(),
                'tag': base64.b64encode(encryptor.tag).decode()
            })
        }

    def decrypt_document(self, 
                        encrypted_content: bytes,
                        encrypted_key: bytes,
                        metadata: str,
                        private_key_encrypted: bytes,
                        master_key: bytes) -> bytes:
        """Entschlüsselt ein Dokument"""
        # Entschlüssele Private Key
        f = Fernet(base64.urlsafe_b64encode(master_key))
        private_pem = f.decrypt(private_key_encrypted)
        private_key = serialization.load_pem_private_key(private_pem, password=None)
        
        # Entschlüssele Document Key
        document_key = private_key.decrypt(
            encrypted_key,
            asymmetric_padding.OAEP(
                mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Entschlüssele Content
        meta = json.loads(metadata)
        nonce = base64.b64decode(meta['nonce'])
        tag = base64.b64decode(meta['tag'])
        
        cipher = Cipher(
            algorithms.AES(document_key),
            modes.GCM(nonce, tag)
        )
        decryptor = cipher.decryptor()
        
        return decryptor.update(encrypted_content) + decryptor.finalize()

    def create_access_token(self, user_id: str) -> str:
        """Erstellt einen JWT Token"""
        expire = datetime.utcnow() + timedelta(
            hours=self.settings.token_validity_hours
        )
        to_encode = {
            "sub": user_id,
            "exp": expire
        }
        return jwt.encode(to_encode, self.jwt_secret, algorithm="HS256")

def verify_password(self, password: str, password_hash: str) -> bool:
        """Verifiziert ein Passwort"""
        salt, stored_hash = password_hash.split(':')
        derived_key = self._derive_key_from_password(
            password, 
            base64.b64decode(salt)
        )
        return base64.b64encode(derived_key).decode() == stored_hash

    def hash_password(self, password: str) -> str:
        """Hasht ein Passwort für die Speicherung"""
        salt = os.urandom(16)
        derived_key = self._derive_key_from_password(password, salt)
        return f"{base64.b64encode(salt).decode()}:{base64.b64encode(derived_key).decode()}"

    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Leitet einen Schlüssel aus einem Passwort ab"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.settings.crypto_iterations,
        )
        return kdf.derive(password.encode())

    def encrypt_preview(self, preview_data: bytes, public_key_pem: bytes) -> bytes:
        """Verschlüsselt eine Dokumentvorschau"""
        preview_key = os.urandom(32)
        cipher = Cipher(
            algorithms.AES(preview_key),
            modes.GCM(os.urandom(12))
        )
        encryptor = cipher.encryptor()
        encrypted_preview = encryptor.update(preview_data) + encryptor.finalize()
        
        # Verschlüssele Preview Key mit Public Key
        public_key = serialization.load_pem_public_key(public_key_pem)
        encrypted_key = public_key.encrypt(
            preview_key,
            asymmetric_padding.OAEP(
                mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Kombiniere für Speicherung
        return base64.b64encode(
            json.dumps({
                'preview': base64.b64encode(encrypted_preview).decode(),
                'key': base64.b64encode(encrypted_key).decode(),
                'nonce': base64.b64encode(encryptor.nonce).decode(),
                'tag': base64.b64encode(encryptor.tag).decode()
            }).encode()
        )