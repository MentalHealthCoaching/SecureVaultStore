# SecureVaultStore

Ein sicheres Ende-zu-Ende verschlüsseltes Dokumentenmanagementsystem mit integrierter Chat- und Briefkastenfunktion.

## Features

- 🔒 Ende-zu-Ende Verschlüsselung aller Dokumente und Nachrichten
- 🔑 Hybride Verschlüsselung (RSA-4096 + AES-256-GCM)
- 👥 Automatische Benutzerregistrierung 
- 🖼️ Verschlüsselte Dokumentenvorschau
- 💬 Verschlüsselte Chat-Funktion (1:1 und Gruppen)
- 📬 Sicheres Briefkastensystem
- 📝 Detaillierte Zugriffsprotokollierung
- 🔄 Passwort-Recovery-System

## Installation

```bash
# Repository klonen
git clone git@github.com:MentalHealthCoaching/SecureVaultStore.git
cd SecureVaultStore

# Python Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
.\venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Konfiguration anpassen
cp config.ini.example config.ini
# Editieren Sie config.ini mit Ihren Einstellungen
```

## Konfiguration

Die `config.ini` enthält alle wichtigen Einstellungen:

```ini
[database]
type = sqlite/mysql/postgresql
host = localhost
port = 3306
database = secure_vault
user = db_user
password = db_password

[storage]
max_file_size_mb = 50
temp_dir = /tmp/secure_vault
data_dir = /var/secure_vault/data

[security]
jwt_secret = your_secret_key
token_validity_hours = 24
min_password_length = 12
```

## API-Dokumentation

Vollständige API-Dokumentation finden Sie unter `/docs` nach dem Start des Servers.

### Wichtige Endpunkte

```http
POST /api/auth
Content-Type: application/json
{
    "user_id": "string",
    "password": "string"
}

POST /api/documents
Authorization: Bearer <token>
Content-Type: multipart/form-data
- file: Binary
- recipients: ["user_id"] (optional)

DELETE /api/documents/{document_id}
Authorization: Bearer <token>
{
    "password": "string"
}
```

## Verzeichnisstruktur

```
SecureVaultStore/
├── config/
│   ├── config.example.ini
│   └── logging.ini
├── secure_vault/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── messages.py
│   │   └── users.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── crypto.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py
│   │   ├── message.py
│   │   └── user.py
│   └── utils/
│       ├── __init__.py
│       └── logging.py
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_crypto.py
│   └── test_database.py
├── README.md
├── requirements.txt
└── main.py
```

## Entwicklung

```bash
# Tests ausführen
pytest

# Development Server starten
uvicorn main:app --reload

# Production Server starten
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Sicherheit

- Alle Daten werden Ende-zu-Ende verschlüsselt
- AES-256-GCM für Dokumentenverschlüsselung
- RSA-4096 für Schlüsselaustausch
- PBKDF2 mit hoher Iterationszahl für Passwort-Hashing
- Keine Masterschlüssel oder Backdoors
- Vollständiges Audit-Logging

## Lizenz

MIT License

## Contributing

Bitte lesen Sie CONTRIBUTING.md für Details zu unserem Code of Conduct und dem Prozess für Pull Requests.
