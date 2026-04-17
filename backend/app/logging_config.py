"""
Logging Configuration for UpSkill AI
Provides file-based logging with rotation
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(app):
    """
    Configure application logging with file handlers
    
    Creates two log files:
    - logs/upskill.log: All logs (INFO and above)
    - logs/errors.log: Error logs only (ERROR and above)
    """
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # File handler for all logs
    file_handler = RotatingFileHandler(
        'logs/upskill.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Error file handler
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s\n'
        'Exception: %(exc_info)s\n'
        '[in %(pathname)s:%(lineno)d]'
    ))
    error_handler.setLevel(logging.ERROR)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info('=' * 60)
    app.logger.info('UpSkill AI Application Started')
    app.logger.info('=' * 60)
    
    return app.logger
