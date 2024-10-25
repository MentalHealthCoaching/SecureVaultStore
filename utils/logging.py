import logging
from logging.handlers import RotatingFileHandler
import os
from secure_vault.core.config import get_settings

settings = get_settings()

def setup_logging():
    """Konfiguriert das Logging-System"""
    log_dir = os.path.join(settings.data_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Hauptlogger
    logger = logging.getLogger('secure_vault')
    logger.setLevel(logging.INFO)
    
    # Datei Handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'secure_vault.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Konsolen Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Handler hinzufügen
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_audit(logger, user_id: str, action: str, success: bool, **kwargs):
    """Erstellt einen Audit-Log-Eintrag"""
    details = {
        'user_id': user_id,
        'action': action,
        'success': success
    }
    details.update(kwargs)
    
    if success:
        logger.info('Audit: %s', details)
    else:
        logger.warning('Audit: %s', details)
