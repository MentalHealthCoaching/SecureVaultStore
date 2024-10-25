```python
class TestAuthentication:
    def test_user_creation_with_valid_password(self, client):
        user_id = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        password = "ValidPassword123!"
        response = client.login(user_id, password)
        
        assert response.status_code == 200
        assert response.json()["new_user"] == True
        assert response.json()["needs_recovery_setup"] == True
        assert "access_token" in response.json()

    def test_user_creation_with_invalid_password(self, client):
        user_id = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        invalid_passwords = [
            "short",  # Zu kurz
            "nouppercaseornumbers",  # Keine Großbuchstaben oder Zahlen
            "NoSpecialChars123",  # Keine Sonderzeichen
            "Only1234567890",  # Nur Zahlen
            "!@#$%^&*()",  # Nur Sonderzeichen
        ]
        
        for password in invalid_passwords:
            response = client.login(user_id, password)
            assert response.status_code == 400
            assert "password" in response.json()["detail"].lower()

class TestRecoverySystem:
    def test_recovery_setup(self, client, test_user):
        # Login
        response = client.login(test_user["user_id"], test_user["password"])
        assert response.status_code == 200
        
        # Get questions
        response = client.session.get(f"{client.base_url}/api/auth/recovery-questions")
        assert response.status_code == 200
        questions = response.json()["questions"]
        
        # Setup recovery with 5 questions
        selected_questions = questions[:5]
        answers = ["Answer123!" for _ in range(5)]
        
        response = client.session.post(
            f"{client.base_url}/api/auth/setup-recovery",
            json={
                "question_answers": [
                    {"question_id": q["id"], "answer": a}
                    for q, a in zip(selected_questions, answers)
                ],
                "current_password": test_user["password"]
            }
        )
        assert response.status_code == 200

        # Verify setup
        response = client.session.get(
            f"{client.base_url}/api/auth/recovery/{test_user['user_id']}/questions"
        )
        assert response.status_code == 200
        assert len(response.json()["questions"]) == 5

class TestDocumentManagement:
    def test_list_documents_pagination(self, client, test_user, test_files):
        # Login
        response = client.login(test_user["user_id"], test_user["password"])
        assert response.status_code == 200
        
        # Upload 25 files
        for i in range(25):
            response = client.upload_file(test_files['small'])
            assert response.status_code == 200
        
        # Test pagination
        page_size = 10
        response = client.session.get(
            f"{client.base_url}/api/documents",
            params={"page": 1, "per_page": page_size}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == page_size
        assert data["total"] == 25
        
        # Test letzte Seite
        response = client.session.get(
            f"{client.base_url}/api/documents",
            params={"page": 3, "per_page": page_size}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 5  # Restliche Dokumente

class TestSecurity:
    def test_rate_limiting_login(self, client):
        user_id = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPassword123!"
        
        # Versuche mehr Logins als erlaubt
        for i in range(10):
            response = client.login(user_id, password)
            if response.status_code == 429:
                rate_limit_hit = True
                break
        
        assert rate_limit_hit
        assert "rate limit" in response.json()["detail"].lower()
        
        # Warte auf Reset
        time.sleep(60)
        
        # Versuche erneut
        response = client.login(user_id, password)
        assert response.status_code in [200, 401]  # Je nachdem ob User existiert

class TestPerformance:
    @pytest.mark.timeout(30)
    def test_response_times(self, client, test_user):
        # Login
        start_time = time.time()
        response = client.login(test_user["user_id"], test_user["password"])
        login_time = time.time() - start_time
        assert login_time < 1.0  # Login sollte unter 1 Sekunde dauern
        
        # Upload small file
        start_time = time.time()
        response = client.upload_file(test_files['small'])
        upload_time = time.time() - start_time
        assert upload_time < 2.0  # Upload sollte unter 2 Sekunden dauern
        
        # List documents
        start_time = time.time()
        response = client.list_files()
        list_time = time.time() - start_time
        assert list_time < 0.5  # Listing sollte unter 0.5 Sekunden dauern
```
