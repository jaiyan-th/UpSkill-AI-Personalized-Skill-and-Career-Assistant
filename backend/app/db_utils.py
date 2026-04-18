"""
Database Utility Functions
Handles database operations with retry logic for lock errors
"""

import psycopg2
import time
from functools import wraps


def retry_on_lock(max_retries=3, delay=0.1):
    """
    Decorator to retry database operations on lock errors
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except psycopg2.OperationalError as e:
                    # Retry on general operational errors or deadlocks in Postgres
                    if "deadlock" in str(e).lower() or "timeout" in str(e).lower():
                        last_error = e
                        if attempt < max_retries - 1:
                            time.sleep(delay * (attempt + 1))  # Exponential backoff
                            continue
                    raise
            # If all retries failed, raise the last error
            if last_error:
                raise last_error
        return wrapper
    return decorator


def execute_with_retry(db, query, params=None, max_retries=3):
    """
    Execute a database query with retry logic
    
    Args:
        db: Database connection
        query: SQL query string
        params: Query parameters (optional)
        max_retries: Maximum number of retry attempts
    
    Returns:
        Query result
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            if params:
                result = db.execute(query, params)
            else:
                result = db.execute(query)
            return result
        except psycopg2.OperationalError as e:
            if "deadlock" in str(e).lower() or "timeout" in str(e).lower():
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
                    continue
            raise
    
    if last_error:
        raise last_error


def commit_with_retry(db, max_retries=3):
    """
    Commit database changes with retry logic
    
    Args:
        db: Database connection
        max_retries: Maximum number of retry attempts
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            db.commit()
            return
        except psycopg2.OperationalError as e:
            if "deadlock" in str(e).lower() or "timeout" in str(e).lower():
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
                    continue
            raise
    
    if last_error:
        raise last_error
