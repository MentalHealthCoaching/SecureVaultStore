# SecureVaultStore JavaScript Client Documentation

## Installation

```bash
# Using npm
npm install secure-vault-client

# Using yarn
yarn add secure-vault-client
```

## Quick Start

```javascript
import { SecureVaultClient } from 'secure-vault-client';

// Initialize client
const client = new SecureVaultClient({
  baseUrl: 'https://api.securevaultstore.com/v1',
  language: 'en'  // 'de', 'en', 'es'
});

// Basic usage
const main = async () => {
  // Login (creates account if not exists)
  const session = await client.login('user@example.com', 'securePassword123!');
  
  // Upload document
  const uploadResult = await client.uploadDocument({
    file: document.getElementById('fileInput').files[0],
    recipientId: 'recipient@example.com'
  });
  
  // List documents
  const documents = await client.listDocuments();
};
```

## Client Class API

### Authentication

```javascript
// Login or create account
const session = await client.login(userId, password);
// Returns: { token, newUser, needsRecoverySetup }

// Change password
await client.changePassword(oldPassword, newPassword);

// Setup recovery questions
const questions = await client.getRecoveryQuestions();
await client.setupRecovery({
  currentPassword: 'current123',
  questionAnswers: [
    { questionId: 1, answer: 'Blue' },
    { questionId: 5, answer: 'Paris' },
    // ... at least 5 questions required
  ]
});

// Recover account
const userQuestions = await client.getRecoveryQuestions('user@example.com');
await client.recoverAccount({
  userId: 'user@example.com',
  answers: ['Blue', 'Paris', ...],
  newPassword: 'newSecurePass123!'
});
```

### Document Management

```javascript
// Upload document
const doc = await client.uploadDocument({
  file: File,           // File object
  recipientId: string,  // Email of recipient
  tags: string[],       // Optional tags
  onProgress: (progress) => console.log(`${progress}%`)  // Optional
});

// List documents
const docs = await client.listDocuments({
  tags: ['work', 'important'],  // Optional
  mimeType: 'application/pdf',  // Optional
  sortBy: 'created_at',        // Optional
  sortOrder: 'desc',           // Optional
  page: 1,                     // Optional
  perPage: 50                  // Optional
});

// Get single document
const doc = await client.getDocument(documentId);

// Delete document
await client.deleteDocument(documentId, currentPassword);
```

## Examples

### Complete User Flow Example

```javascript
const completeFlow = async () => {
  try {
    // Initialize client
    const client = new SecureVaultClient({
      baseUrl: 'https://api.securevaultstore.com/v1',
      language: 'en'
    });

    // Login
    const { token, newUser, needsRecoverySetup } = await client.login(
      'user@example.com',
      'securePass123!'
    );

    // If new user or recovery not set up
    if (needsRecoverySetup) {
      // Get available questions
      const questions = await client.getRecoveryQuestions();
      
      // Setup recovery
      await client.setupRecovery({
        currentPassword: 'securePass123!',
        questionAnswers: [
          { questionId: 1, answer: 'Blue' },
          { questionId: 5, answer: 'Paris' },
          { questionId: 12, answer: 'Pizza' },
          { questionId: 15, answer: 'Rex' },
          { questionId: 23, answer: '1999' }
        ]
      });
    }

    // Upload document with progress
    const uploadResult = await client.uploadDocument({
      file: myFile,
      recipientId: 'colleague@example.com',
      tags: ['project-x', '2024'],
      onProgress: (progress) => {
        updateProgressBar(progress);
      }
    });

    // List all PDF documents
    const docs = await client.listDocuments({
      mimeType: 'application/pdf',
      sortBy: 'created_at',
      sortOrder: 'desc'
    });

  } catch (error) {
    if (error.code === 'RATE_LIMIT_EXCEEDED') {
      console.error('Please wait before trying again');
    } else {
      console.error('Error:', error.message);
    }
  }
};
```

### Error Handling Example

```javascript
class DocumentUploader {
  constructor(client) {
    this.client = client;
  }

  async uploadWithRetry(file, recipientId, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.client.uploadDocument({
          file,
          recipientId,
          onProgress: (progress) => {
            this.updateProgress(progress);
          }
        });
      } catch (error) {
        if (error.code === 'RATE_LIMIT_EXCEEDED') {
          if (attempt === maxRetries) throw error;
          await this.sleep(Math.pow(2, attempt) * 1000);
          continue;
        }
        throw error;
      }
    }
  }

  updateProgress(progress) {
    // Update UI
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### React Component Example

```jsx
import { useSecureVault } from 'secure-vault-client/react';

function DocumentList() {
  const { documents, loading, error, fetchDocuments } = useSecureVault();
  
  useEffect(() => {
    fetchDocuments({
      tags: ['important'],
      sortBy: 'created_at'
    });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {documents.map(doc => (
        <DocumentItem 
          key={doc.id} 
          document={doc} 
          onDelete={() => handleDelete(doc.id)} 
        />
      ))}
    </div>
  );
}
```

## Events

The client emits various events you can listen to:

```javascript
client.on('upload:progress', (progress) => {
  console.log(`Upload progress: ${progress}%`);
});

client.on('session:expired', () => {
  console.log('Session expired, please login again');
});

client.on('rate:limit', (resetTime) => {
  console.log(`Rate limit hit, reset at: ${resetTime}`);
});
```

## Configuration Options

```javascript
const client = new SecureVaultClient({
  baseUrl: string,          // API base URL
  language: 'en'|'de'|'es', // Default language
  timeout: number,          // Request timeout in ms
  retryAttempts: number,    // Number of retry attempts
  debug: boolean,           // Enable debug logging
  onError: (error) => {},   // Global error handler
  rateLimitHandler: (resetTime) => {} // Custom rate limit handler
});
```

## Security Best Practices

1. **Token Storage**
   ```javascript
   // DO store tokens securely
   sessionStorage.setItem('token', token);
   
   // DON'T store in localStorage
   // localStorage.setItem('token', token); // Not recommended
   ```

2. **Password Handling**
   ```javascript
   // DO clear passwords from memory
   const login = async (userId, password) => {
    try {
      await client.login(userId, password);
    } finally {
      password = null;
    }
   };
   ```

3. **Error Messages**
   ```javascript
   // DO use generic error messages in UI
   catch (error) {
     if (error.code === 'AUTH_FAILED') {
       showError('Invalid credentials');
     }
   }
   ```

## Rate Limiting Handling

```javascript
// Automatic retry with exponential backoff
const client = new SecureVaultClient({
  retryAttempts: 3,
  retryDelay: 1000, // Base delay in ms
  rateLimitHandler: async (resetTime) => {
    const waitTime = new Date(resetTime) - new Date();
    await new Promise(resolve => setTimeout(resolve, waitTime));
    return true; // Retry after waiting
  }
});
```

## Support

For issues and feature requests, visit:
- GitHub: [github.com/SecureVaultStore/js-client](http://example.com)
- Documentation: [docs.securevaultstore.com](http://example.com)

