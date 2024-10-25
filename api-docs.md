# SecureVaultStore API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Document Management](#document-management)
4. [User Management](#user-management)
5. [Recovery System](#recovery-system)
6. [Security Considerations](#security-considerations)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)

## Overview

The SecureVaultStore API provides end-to-end encrypted document storage with secure sharing capabilities. All data is encrypted before storage, and the server never has access to unencrypted content.

### Base URL
```
https://api.securevaultstore.com/v1
```

### Common Headers
```http
Authorization: Bearer <token>
Content-Type: application/json
```

## Authentication

### Login / Register
```http
POST /api/auth
Content-Type: application/json

Request:
{
    "user_id": "string",
    "password": "string"
}

Response (200 OK):
{
    "access_token": "string",
    "token_type": "bearer",
    "new_user": boolean,
    "needs_recovery_setup": boolean
}
```

### Change Password
```http
POST /api/auth/change-password
Authorization: Bearer <token>

Request:
{
    "old_password": "string",
    "new_password": "string"
}

Response (200 OK):
{
    "message": "Password successfully changed"
}
```

## Document Management

### Upload Document
```http
POST /api/documents
Authorization: Bearer <token>
Content-Type: multipart/form-data

Request Parameters:
- file: Binary file
- name: string
- recipient_id: string
- mime_type: string (optional)

Response (200 OK):
{
    "document_id": "string",
    "recipient_id": "string",
    "created_at": "datetime",
    "status": "delivered"
}
```

### List Documents
```http
GET /api/documents
Authorization: Bearer <token>

Query Parameters:
- path_prefix?: string
- tags?: string (comma-separated)
- mime_type?: string
- created_after?: datetime
- created_before?: datetime
- sort_by?: string (created_at, modified_at, file_size)
- sort_order?: string (asc, desc)
- page?: integer
- per_page?: integer

Response (200 OK):
{
    "documents": [
        {
            "document_id": "string",
            "owner_id": "string",
            "name": "string",
            "created_at": "datetime",
            "modified_at": "datetime",
            "last_access": "datetime",
            "mime_type": "string",
            "tags": ["string"],
            "file_size": integer
        }
    ],
    "total": integer,
    "page": integer,
    "per_page": integer
}
```

### Get Document
```http
GET /api/documents/{document_id}
Authorization: Bearer <token>

Response (200 OK):
{
    "document_id": "string",
    "owner_id": "string",
    "name": "string",
    "created_at": "datetime",
    "modified_at": "datetime",
    "last_access": "datetime",
    "mime_type": "string",
    "tags": ["string"],
    "content": "binary"
}
```

### Delete Document
```http
DELETE /api/documents/{document_id}
Authorization: Bearer <token>

Request:
{
    "password": "string"
}

Response (200 OK):
{
    "status": "success"
}
```

## Recovery System

### Get Available Recovery Questions
```http
GET /api/auth/recovery-questions
Query Parameters:
- lang: string (de|en|es, default: en)

Response (200 OK):
{
    "questions": [
        {
            "id": integer,
            "question": "string"
        }
    ]
}
```

### Setup Recovery Questions
```http
POST /api/auth/setup-recovery
Authorization: Bearer <token>

Request:
{
    "question_answers": [
        {
            "question_id": integer,
            "answer": "string"
        }
    ],
    "current_password": "string"
}

Response (200 OK):
{
    "message": "Recovery questions successfully set up"
}
```

### Get User's Recovery Questions
```http
GET /api/auth/recovery/{user_id}/questions
Query Parameters:
- lang: string (de|en|es, default: en)

Response (200 OK):
{
    "questions": ["string"]
}
```

### Verify Recovery Answers
```http
POST /api/auth/recovery/{user_id}/verify

Request:
{
    "answers": ["string"],
    "new_password": "string"
}

Response (200 OK):
{
    "message": "Password successfully reset"
}
```

## File Properties

### Supported File Types
- All common document formats (PDF, DOCX, etc.)
- Images (PNG, JPEG, GIF, etc.)
- Text files
- Archives (ZIP, RAR, etc.)
- Maximum file size: 50MB (configurable)

### Document Tags
⚠️ **WARNING**: Tags are stored unencrypted to enable searching. Never include sensitive information in tags!

Good tag examples:
- ✅ "work", "personal", "archived"
- ✅ "2023", "Q4", "draft"
- ❌ Don't use: client names, project codes, sensitive data

## Security Considerations

### Password Requirements
- Length: 12-64 characters
- Must contain:
  * Lower and uppercase letters
  * At least one number
  * At least one special character (max 3)
- Must not:
  * Be too complex to remember
  * Be a common password
  * Follow simple patterns

### Recovery System Requirements
- 5 questions must be selected
- 4 correct answers needed for recovery
- Available in multiple languages (DE, EN, ES)
- Questions designed for unique, memorable answers

### Encryption
- AES-256-GCM for document encryption
- RSA-4096 for key exchange
- PBKDF2 with high iteration count for password hashing
- Unique encryption key per document

## Rate Limiting

### Per IP Address
- 100 requests per minute globally

### Per Action
- Login: 5 attempts per minute
- Document upload: 10 per minute
- Document download: 50 per minute
- Password changes: 1 per minute
- Recovery attempts: 3 per hour

## Error Handling

All errors follow this format:
```json
{
    "detail": "Error description",
    "error_code": "ERROR_CODE",
    "field_errors": [
        {
            "field": "field_name",
            "error": "error_description"
        }
    ]
}
```

### Common Status Codes
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 413: Payload Too Large
- 429: Too Many Requests
- 500: Internal Server Error

## Client Implementation Notes

### Document Upload Example
```python
import requests

def upload_document(file_path: str, recipient_id: str, token: str):
    with open(file_path, 'rb') as f:
        response = requests.post(
            'https://api.securevaultstore.com/v1/api/documents',
            files={'file': f},
            data={
                'recipient_id': recipient_id,
                'name': os.path.basename(file_path)
            },
            headers={'Authorization': f'Bearer {token}'}
        )
    return response.json()
```

### Error Handling Example
```python
try:
    response = requests.post(url, data=data)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    error_data = e.response.json()
    print(f"Error: {error_data['detail']}")
```

## Language Support

The API supports the following languages for recovery questions:
- 🇩🇪 German (de)
- 🇬🇧 English (en)
- 🇪🇸 Spanish (es)

All system messages and errors are in English by default.

## Support

For API support or to report security issues:
- Email: api-support@securevaultstore.com
- Security: security@securevaultstore.com

Documentation last updated: 2024-02-20