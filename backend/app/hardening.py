"""
System Hardening Module
Implements rate limiting, logging, and security enhancements
"""

import os
import logging
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict
import threading

# ─── Rate Limiting ────────────────────────────────────────────────────────────

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
        
    def is_allowed(self, key, max_requests=100, window_seconds=60):
        """
        Check if request is allowed based on rate limit
        
        Args:
            key: Unique identifier (e.g., IP address or user ID)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            bool: True if request is allowed, False otherwise
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        with self.lock:
            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
            
            # Check if limit exceeded
            if len(self.requests[key]) >= max_requests:
                return False
            
            # Add current request
            self.requests[key].append(now)
            return True
    
    def get_remaining(self, key, max_requests=100, window_seconds=60):
        """Get remaining requests in current window"""
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        with self.lock:
            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
            
            return max(0, max_requests - len(self.requests[key]))

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_requests=100, window_seconds=60, key_func=None):
    """
    Rate limiting decorator
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        key_func: Function to generate rate limit key (default: IP address)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get rate limit key
            if key_func:
                key = key_func()
            else:
                key = request.remote_addr
            
            # Check rate limit
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                remaining = rate_limiter.get_remaining(key, max_requests, window_seconds)
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': 'Too many requests. Please try again later.',
                        'details': {
                            'retry_after': window_seconds,
                            'remaining': remaining
                        }
                    }
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ─── Logging Configuration ────────────────────────────────────────────────────

def setup_logging(app):
    """
    Configure application logging
    
    Args:
        app: Flask application instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure file handler for general logs
    file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    
    # Configure file handler for error logs
    error_handler = logging.FileHandler(os.path.join(log_dir, 'error.log'))
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s\n'
        'Path: %(pathname)s:%(lineno)d\n'
        'Exception: %(exc_info)s\n'
    ))
    
    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)
    
    # Log startup
    app.logger.info('Application started')
    
    return app

# ─── Request Logging ──────────────────────────────────────────────────────────

def log_request(f):
    """Decorator to log API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log request
        logging.info(f'Request: {request.method} {request.path} from {request.remote_addr}')
        
        # Execute function
        response = f(*args, **kwargs)
        
        # Log response status
        if hasattr(response, 'status_code'):
            logging.info(f'Response: {response.status_code} for {request.path}')
        
        return response
    return decorated_function

# ─── Security Headers ─────────────────────────────────────────────────────────

def add_security_headers(response):
    """Add security headers to response"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# ─── Environment Validation ───────────────────────────────────────────────────

def validate_environment():
    """
    Validate required environment variables
    
    Returns:
        tuple: (bool, list) - (is_valid, missing_vars)
    """
    required_vars = [
        'GROQ_API_KEY',
        'JWT_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return len(missing_vars) == 0, missing_vars

# ─── CORS Configuration ───────────────────────────────────────────────────────

def get_cors_config(environment='development'):
    """
    Get CORS configuration based on environment
    
    Args:
        environment: 'development' or 'production'
        
    Returns:
        dict: CORS configuration
    """
    if environment == 'production':
        # Restrict CORS in production
        return {
            'origins': os.getenv('ALLOWED_ORIGINS', 'http://localhost:8000').split(','),
            'supports_credentials': True,
            'allow_headers': ['Content-Type', 'Authorization'],
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        }
    else:
        # Allow frontend origins in development
        allowed = os.getenv('CORS_ORIGINS', 'http://localhost:5174,http://127.0.0.1:5174').split(',')
        return {
            'origins': [o.strip() for o in allowed],
            'supports_credentials': True,
            'allow_headers': ['Content-Type', 'Authorization'],
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        }

# ─── Input Sanitization ───────────────────────────────────────────────────────

def sanitize_input(text, max_length=10000):
    """
    Sanitize user input
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ''
    
    # Convert to string
    text = str(text)
    
    # Trim to max length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

# ─── Error Tracking ───────────────────────────────────────────────────────────

class ErrorTracker:
    """Track and log errors"""
    
    def __init__(self):
        self.errors = []
        self.max_errors = 100
        
    def log_error(self, error, context=None):
        """Log an error with context"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': str(error),
            'type': type(error).__name__,
            'context': context or {}
        }
        
        self.errors.append(error_entry)
        
        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        # Log to file
        logging.error(f'Error: {error}', extra={'context': context})
    
    def get_recent_errors(self, count=10):
        """Get recent errors"""
        return self.errors[-count:]

# Global error tracker
error_tracker = ErrorTracker()

# ─── Health Check ─────────────────────────────────────────────────────────────

def check_system_health():
    """
    Check system health
    
    Returns:
        dict: Health status
    """
    health = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Check environment variables
    env_valid, missing_vars = validate_environment()
    health['checks']['environment'] = {
        'status': 'ok' if env_valid else 'error',
        'missing_vars': missing_vars
    }
    
    # Check database (if applicable)
    try:
        from .database import get_db
        db = get_db()
        db.execute('SELECT 1').fetchone()
        health['checks']['database'] = {'status': 'ok'}
    except Exception as e:
        health['checks']['database'] = {'status': 'error', 'error': str(e)}
        health['status'] = 'degraded'
    
    # Check LLM service
    try:
        groq_key = os.getenv('GROQ_API_KEY')
        health['checks']['llm'] = {
            'status': 'ok' if groq_key else 'error',
            'message': 'API key configured' if groq_key else 'API key missing'
        }
    except Exception as e:
        health['checks']['llm'] = {'status': 'error', 'error': str(e)}
    
    return health
