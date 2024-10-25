# SecureVaultStore API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Document Management](#document-management)
4. [Tags and Search](#tags-and-search)
5. [Path Management](#path-management)
6. [Document Upload External System](#Document-Upload-for-External-Systems)
7. [Messaging System](#messaging-system)
8. [Client-Side Encryption](#client-side-encryption)
9. [Security Considerations](#security-considerations)
10. [Error Handling](#error-handling)
11. [Rate Limiting](#rate-limiting)
12. [Implementation Examples](#implementation-examples)

## Overview

SecureVaultStore provides a secure, end-to-end encrypted document storage and messaging system with two operational modes:
- Direct API access with client-side encryption
- Simplified mailbox mode for secure document exchange with external systems

### Key Features

- End-to-end encryption of all documents and messages
- Secure document name encryption
- Automatic user registration
- Document sharing and management
- Encrypted messaging
- Tag-based document organization
- Encrypted path hierarchy
- Document preview generation
- Secure mailbox functionality

## Authentication

All endpoints (except /api/auth) require Bearer token authentication.

```http
Authorization: Bearer <token>
```

### Get Access Token

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
    "new_user": boolean
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
- encrypted_name: string  // Encrypted document name
- encrypted_path?: string
- tags?: string[]  // Array of tags (non-sensitive!)
- recipients?: string[]  // Array of user IDs to share with

Response (200 OK):
{
    "document_id": "string",
    "owner_id": "string",
    "encrypted_name": "string",
    "created_at": "datetime",
    "modified_at": "datetime",
    "mime_type": "string",
    "encrypted_path": "string",
    "tags": ["string"],
    "file_size": integer,
    "encrypted_preview": "string" // Base64 encoded if available
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
    "encrypted_name": "string",
    "created_at": "datetime",
    "modified_at": "datetime",
    "last_access": "datetime",
    "mime_type": "string",
    "encrypted_path": "string",
    "tags": ["string"],
    "encrypted_content": "string",
    "encrypted_preview": "string"
}
```

### List Documents

```http
GET /api/documents
Authorization: Bearer <token>

Query Parameters:
- path_prefix?: string (encrypted)
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
            "encrypted_name": "string",
            "created_at": "datetime",
            "modified_at": "datetime",
            "last_access": "datetime",
            "mime_type": "string",
            "encrypted_path": "string",
            "tags": ["string"],
            "encrypted_preview": "string",
            "file_size": integer
        }
    ],
    "total": integer,
    "page": integer,
    "per_page": integer
}
```

### Delete Document

```http
DELETE /api/documents/{document_id}
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
    "password": "string"  // Current user password required
}

Response (200 OK):
{
    "status": "success"
}
```

## Document Upload for External Systems

External systems (eg mailbox mode) can upload documents for users without participating in the encryption system.

### Upload Document for User

```http
POST /api/documents
Authorization: Bearer <token>
Content-Type: multipart/form-data

Request Parameters:
- file: Binary file
- name: string           // Plain text name, will be encrypted by server
- recipient_id: string   // User who should receive the document
- mime_type: string     // Optional, will be detected if not provided

Response (200 OK):
{
    "document_id": "string",
    "recipient_id": "string",
    "created_at": "datetime",
    "status": "delivered"
}
```

The server will:
1. Generate a new document_key
2. Encrypt the document with this key
3. Encrypt the document name with the document_key
4. Encrypt the document_key with the recipient's public key
5. Store the encrypted document, name and key

### Implementation Example

```python
def deliver_document(file_path: str, recipient_id: str):
    with open(file_path, 'rb') as f:
        filename = os.path.basename(file_path)
        response = requests.post(
            '/api/documents',
            files={'file': f},
            data={
                'name': filename,          # Plain text name
                'recipient_id': recipient_id
            },
            headers={'Authorization': f'Bearer {token}'}
        )
    return response.json()
```

### Security Notes

1. Document names are transmitted in plain text but encrypted at rest
2. Authorization token should have limited permissions
3. Transport encryption (HTTPS) ensures secure transmission
4. Server handles all cryptographic operations
5. External systems never have access to the encryption keys or encrypted content

This approach allows external systems to safely deliver documents into the secure vault without having to implement any cryptographic operations themselves.

## Tags and Search

⚠️ **SECURITY WARNING**: Tags are stored unencrypted to enable searching. Never include sensitive information in tags!

### Search Documents

```http
GET /api/documents/search
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
    "tags": ["tag1", "tag2"],
    "require_all_tags": boolean,
    "exclude_tags": ["tag3"],
    "mime_type": "string",
    "created_after": "datetime",
    "created_before": "datetime",
    "sort_by": "string",
    "sort_order": "string"
}

Response (200 OK): Same as List Documents
```

## Client-Side Encryption

### Java Implementation Example

```java
public class SecureVaultClient {
    private final SecretKey masterKey;
    private final KeyPair rsaKeyPair;
    
    public byte[] encryptDocument(byte[] content, String name) throws Exception {
        // Generate document key
        SecretKey docKey = generateAESKey();
        
        // Encrypt content
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        byte[] iv = generateIV();
        cipher.init(Cipher.ENCRYPT_MODE, docKey, new GCMParameterSpec(128, iv));
        
        // Add name to AAD (Additional Authenticated Data)
        cipher.updateAAD(name.getBytes(StandardCharsets.UTF_8));
        
        byte[] encryptedContent = cipher.doFinal(content);
        byte[] encryptedKey = encryptDocumentKey(docKey);
        
        return combineEncryptedData(iv, encryptedKey, encryptedContent);
    }
    
    public String encryptName(String name) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        byte[] iv = generateIV();
        cipher.init(Cipher.ENCRYPT_MODE, masterKey, new GCMParameterSpec(128, iv));
        
        byte[] encryptedName = cipher.doFinal(name.getBytes(StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(
            combineEncryptedData(iv, encryptedName)
        );
    }
}
```

### Python Implementation Example

```python
class SecureVaultClient:
    def __init__(self, master_key, rsa_keypair):
        self.master_key = master_key
        self.rsa_keypair = rsa_keypair
    
    def encrypt_document(self, content: bytes, name: str) -> bytes:
        # Generate document key
        doc_key = os.urandom(32)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(doc_key),
            modes.GCM(os.urandom(12))
        )
        encryptor = cipher.encryptor()
        
        # Add name as AAD
        encryptor.authenticate_additional_data(name.encode())
        
        # Encrypt content
        encrypted_content = encryptor.update(content) + encryptor.finalize()
        
        # Encrypt document key
        encrypted_key = self.encrypt_key(doc_key)
        
        return self.combine_encrypted_data(
            encryptor.nonce,
            encrypted_key,
            encrypted_content,
            encryptor.tag
        )
```

## Security Considerations

### 1. End-to-End Encryption
- All documents and names are encrypted before transmission
- Server never has access to unencrypted content
- Each document has its own encryption key

### 2. Client Implementation Options

#### Option 1: Use Dropbox Mode (Recommended)
```java
// Simple and safe upload
DropboxUpload upload = client.uploadToDropbox(file, "document.pdf", recipientId);
String dropboxId = upload.getDropboxId();
String accessKey = upload.getAccessKey();
```

#### Option 2: Use Official Client Library
```java
SecureVaultClient client = SecureVaultClient.builder()
    .withCredentials(userId, password)
    .withKeyStore(keyStore)
    .build();

client.uploadDocument(file, "document.pdf");
```

### 3. Tags Security
- Tags are unencrypted for searchability
- Never include sensitive data in tags
- Safe tag examples:
  - ✅ "work", "personal", "archived"
  - ✅ "2023", "Q4", "draft"
  - ❌ Don't use: client names, project codes, sensitive data

## Rate Limiting

- 100 requests per minute per IP
- 1000 requests per hour per user
- File upload: 50MB per file (configurable)
- Maximum 50 tags per document
- Maximum 64 characters per tag

## Error Handling

```json
{
    "detail": "Error description",
    "error_code": "string",
    "field_errors": [
        {
            "field": "string",
            "error": "string"
        }
    ]
}
```

Common Status Codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 413: Payload Too Large
- 500: Internal Server Error

---

For more information or support, contact the development team or refer to the repository documentation.
