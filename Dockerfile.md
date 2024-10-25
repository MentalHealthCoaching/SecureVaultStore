# Verwende offizielles Python-Image
FROM python:3.11-slim

# Setze Arbeitsverzeichnis
WORKDIR /app

# Kopiere Requirements und installiere Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere Anwendungscode
COPY . .

# Erstelle notwendige Verzeichnisse
RUN mkdir -p /var/secure_vault/data /var/secure_vault/logs

# Setze Umgebungsvariablen
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Exponiere Port
EXPOSE 8000

# Starte Anwendung
CMD ["uvicorn", "secure_vault.main:app", "--host", "0.0.0.0", "--port", "8000"]
