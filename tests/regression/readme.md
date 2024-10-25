# SecureVaultStore Regression Tests

Diese Tests überprüfen die grundlegende Funktionalität des SecureVaultStore API.

## Setup

```bash
# Virtualenv erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # oder auf Windows: .\venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt
```

## Tests ausführen

```bash
# Alle Tests ausführen
pytest

# Tests mit spezifischer API-URL
pytest --api-url=http://test-server:8000

# Tests mit spezifischer Dateigröße
pytest --test-file-size=1048576  # 1MB

# Verbose Output
pytest -v

# Spezifischen Test ausführen
pytest test_basic_workflow.py::test_complete_workflow -v
```

## Test Cases

1. **Complete Workflow Test**
   - Upload als neuer User
   - Versuch mit falschem Passwort
   - Dateiliste prüfen
   - Download und Vergleich
   - Löschung
   - Leere Dateiliste prüfen

2. **Upload Test**
   - Nur Upload-Prozess
   - Erfolgreicher Upload = 200

3. **Invalid Login Test**
   - Login mit falschen Credentials
   - Erwarteter 401 Error

4. **File Operations Test**
   - Alle Dateioperationen in Sequenz
   - Upload, List, Download, Delete

5. **File Comparison Test**
   - Tests mit verschiedenen Dateigrößen
   - Byte-für-Byte Vergleich

## Logging

Logs werden in `test_logs` gespeichert:
- test_run_{timestamp}.log
- Fehlerdetails
- Response Times
- HTTP Status Codes

## Requirements

```
pytest==7.4.4
requests==2.31.0
pytest-asyncio==0.23.3
pytest-xdist==3.5.0
```
