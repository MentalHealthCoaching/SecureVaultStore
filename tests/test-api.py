import pytest
from fastapi.testclient import TestClient
from secure_vault.main import app
from secure_vault.core.database import get_db
import os
import tempfile
from typing import Generator

@pytest.fixture
def test_db():
    # Temporäre SQLite Datenbank für Tests
    tmp_db = tempfile.NamedTemporaryFile(delete=False)
    
    # Override database dependency
    def override_get_db() -> Generator:
        try:
            db = TestingSessionLocal(bind=engine)
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield tmp_db.name
    
    os.unlink(tmp_db.name)

@pytest.fixture
def client(test_db):
    return TestClient(app)

def test_user_authentication(client):
    # Test Benutzerregistrierung
    response = client.post(
        "/api/auth",
        json={"user_id": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["new_user"] is True
    
    # Test Login mit falschen Credentials
    response = client.post(
        "/api/auth",
        json={"user_id": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 401

def test_document_upload(client, test_db):
    # Erst Benutzer erstellen und einloggen
    auth_response = client.post(
        "/api/auth",
        json={"user_id": "testuser", "password": "testpass123"}
    )
    token = auth_response.json()["access_token"]
    
    # Test Dokument-Upload
    test_file = tempfile.NamedTemporaryFile(delete=False)
    test_file.write(b"Test content")
    test_file.close()
    
    with open(test_file.name, 'rb') as f:
        response = client.post(
            "/api/documents",
            files={"file": ("test.txt", f, "text/plain")},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    assert "document_id" in response.json()
    
    os.unlink(test_file.name)

def test_document_deletion(client, test_db):
    # Setup: Benutzer erstellen und Dokument hochladen
    auth_response = client.post(
        "/api/auth",
        json={"user_id": "testuser", "password": "testpass123"}
    )
    token = auth_response.json()["access_token"]
    
    # Dokument hochladen
    test_file = tempfile.NamedTemporaryFile(delete=False)
    test_file.write(b"Test content")
    test_file.close()
    
    with open(test_file.name, 'rb') as f:
        upload_response = client.post(
            "/api/documents",
            files={"file": ("test.txt", f, "text/plain")},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    document_id = upload_response.json()["document_id"]
    
    # Test Löschung mit falschem Passwort
    response = client.delete(
        f"/api/documents/{document_id}",
        json={"password": "wrongpass"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    
    # Test Löschung mit korrektem Passwort
    response = client.delete(
        f"/api/documents/{document_id}",
        json={"password": "testpass123"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    os.unlink(test_file.name)
