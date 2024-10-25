import pytest
import requests
import os
import hashlib
from typing import Tuple
import uuid
import tempfile

class SecureVaultTestClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.session = requests.Session()
    
    def login(self, user_id: str, password: str) -> dict:
        response = self.session.post(
            f"{self.base_url}/api/auth",
            json={"user_id": user_id, "password": password}
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
        return response
    
    def upload_file(self, file_path: str) -> dict:
        with open(file_path, 'rb') as f:
            response = self.session.post(
                f"{self.base_url}/api/documents",
                files={"file": f},
                data={
                    "name": os.path.basename(file_path),
                }
            )
        return response
    
    def list_files(self) -> dict:
        response = self.session.get(
            f"{self.base_url}/api/documents"
        )
        return response
    
    def download_file(self, document_id: str) -> Tuple[int, bytes]:
        response = self.session.get(
            f"{self.base_url}/api/documents/{document_id}"
        )
        return response.status_code, response.content
    
    def delete_file(self, document_id: str, password: str) -> dict:
        response = self.session.delete(
            f"{self.base_url}/api/documents/{document_id}",
            json={"password": password}
        )
        return response

def create_test_file(content: bytes = None) -> str:
    """Erstellt eine Testdatei und gibt den Pfad zurück"""
    if content is None:
        content = os.urandom(1024)  # 1KB zufällige Daten
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        return tmp.name

def get_file_hash(file_path: str) -> str:
    """Berechnet den SHA256 Hash einer Datei"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

@pytest.fixture
def client():
    """Test Client Fixture"""
    return SecureVaultTestClient("http://localhost:8000")

@pytest.fixture
def test_user():
    """Generiert eindeutige Test-User-Daten"""
    return {
        "user_id": f"test_user_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!"
    }

@pytest.fixture
def test_file():
    """Erstellt eine Testdatei und räumt sie nach dem Test auf"""
    file_path = create_test_file()
    yield file_path
    try:
        os.unlink(file_path)
    except:
        pass

def test_complete_workflow(client, test_user, test_file):
    """Test des kompletten Workflows von Upload bis Löschung"""
    
    # 1. Upload als neuer User
    response = client.login(test_user["user_id"], test_user["password"])
    assert response.status_code == 200
    assert response.json()["new_user"] == True
    
    response = client.upload_file(test_file)
    assert response.status_code == 200
    document_id = response.json()["document_id"]
    
    # 2. Login mit falschem Passwort
    wrong_client = SecureVaultTestClient("http://localhost:8000")
    response = wrong_client.login(test_user["user_id"], "WrongPassword123!")
    assert response.status_code == 401
    
    # 3. Prüfe ob Datei in der Liste erscheint
    response = client.list_files()
    assert response.status_code == 200
    files = response.json()["documents"]
    assert len(files) == 1
    assert files[0]["document_id"] == document_id
    
    # 4. Datei herunterladen und vergleichen
    status_code, downloaded_content = client.download_file(document_id)
    assert status_code == 200
    
    # Speichere heruntergeladene Datei temporär
    downloaded_file = create_test_file(downloaded_content)
    try:
        # Vergleiche Hashes
        original_hash = get_file_hash(test_file)
        downloaded_hash = get_file_hash(downloaded_file)
        assert original_hash == downloaded_hash
    finally:
        os.unlink(downloaded_file)
    
    # 5. Datei löschen
    response = client.delete_file(document_id, test_user["password"])
    assert response.status_code == 200
    
    # 6. Prüfe ob keine Dateien mehr vorhanden sind
    response = client.list_files()
    assert response.status_code == 200
    files = response.json()["documents"]
    assert len(files) == 0

def test_upload_workflow(client, test_user, test_file):
    """Test nur des Upload-Prozesses"""
    response = client.login(test_user["user_id"], test_user["password"])
    assert response.status_code == 200
    
    response = client.upload_file(test_file)
    assert response.status_code == 200

def test_invalid_login(client, test_user):
    """Test von ungültigem Login"""
    response = client.login(test_user["user_id"], "WrongPassword123!")
    assert response.status_code == 401

def test_file_operations(client, test_user, test_file):
    """Test der Dateioperationen"""
    # Login
    response = client.login(test_user["user_id"], test_user["password"])
    assert response.status_code == 200
    
    # Upload
    response = client.upload_file(test_file)
    assert response.status_code == 200
    document_id = response.json()["document_id"]
    
    # List
    response = client.list_files()
    assert response.status_code == 200
    assert len(response.json()["documents"]) == 1
    
    # Download
    status_code, content = client.download_file(document_id)
    assert status_code == 200
    
    # Delete
    response = client.delete_file(document_id, test_user["password"])
    assert response.status_code == 200
    
    # Verify deletion
    response = client.list_files()
    assert response.status_code == 200
    assert len(response.json()["documents"]) == 0

def test_file_comparison(client, test_user):
    """Test des Dateivergleichs mit verschiedenen Dateigrößen"""
    # Test mit verschiedenen Dateigrößen
    sizes = [1024, 1024*1024, 5*1024*1024]  # 1KB, 1MB, 5MB
    
    for size in sizes:
        # Erstelle Testdatei mit spezifischer Größe
        content = os.urandom(size)
        test_file = create_test_file(content)
        
        try:
            # Login wenn nötig
            if not client.token:
                response = client.login(test_user["user_id"], test_user["password"])
                assert response.status_code == 200
            
            # Upload
            response = client.upload_file(test_file)
            assert response.status_code == 200
            document_id = response.json()["document_id"]
            
            # Download und Vergleich
            status_code, downloaded_content = client.download_file(document_id)
            assert status_code == 200
            assert len(downloaded_content) == size
            assert hashlib.sha256(content).hexdigest() == \
                   hashlib.sha256(downloaded_content).hexdigest()
            
            # Cleanup
            response = client.delete_file(document_id, test_user["password"])
            assert response.status_code == 200
            
        finally:
            os.unlink(test_file)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
