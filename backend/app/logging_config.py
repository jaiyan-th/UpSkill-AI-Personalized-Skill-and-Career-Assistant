"""
Logging Configuration for UpSkill AI
Provides file-based logging with rotation
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(app):
    """
    Configure application logging for local & cloud environments
    """
    app.logger.setLevel(logging.INFO)
    
    # Console handler for cloud & dev logging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    
    try:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'upskill.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, 'errors.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=10
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s\n'
            'Exception: %(exc_info)s\n'
            '[in %(pathname)s:%(lineno)d]'
        ))
        error_handler.setLevel(logging.ERROR)
        
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
    except Exception as e:
        app.logger.warning(f"File loggers disabled: {e}")

    app.logger.info('=' * 60)
    app.logger.info('UpSkill AI Application Started')
    app.logger.info('=' * 60)
    
    return app.logger

