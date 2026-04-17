"""
Simple LLM Response Cache
Reduces API calls by caching responses for identical requests
"""

import hashlib
import json
from functools import wraps
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Simple in-memory cache
# For production, use Redis or Memcached
_cache = {}
_cache_stats = {"hits": 0, "misses": 0}


def cache_llm_response(ttl_minutes=60):
    """
    Decorator to cache LLM responses
    
    Args:
        ttl_minutes: Time to live in minutes (default: 60)
    
    Usage:
        @cache_llm_response(ttl_minutes=30)
        def analyze_resume(resume_text, job_description):
            # ... LLM call
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key_data = {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            cache_key = hashlib.md5(
                json.dumps(cache_key_data, sort_keys=True).encode()
            ).hexdigest()
            
            # Check cache
            if cache_key in _cache:
                cached_data, cached_time = _cache[cache_key]
                age = datetime.now() - cached_time
                
                if age < timedelta(minutes=ttl_minutes):
                    _cache_stats["hits"] += 1
                    logger.info(f"Cache HIT for {func.__name__} (age: {age.seconds}s)")
                    return cached_data
                else:
                    # Expired, remove from cache
                    del _cache[cache_key]
            
            # Cache miss - call function
            _cache_stats["misses"] += 1
            logger.info(f"Cache MISS for {func.__name__}")
            
            result = func(*args, **kwargs)
            
            # Store in cache
            _cache[cache_key] = (result, datetime.now())
            
            return result
        
        return wrapper
    return decorator


def clear_cache():
    """Clear all cached responses"""
    global _cache
    count = len(_cache)
    _cache = {}
    logger.info(f"Cache cleared ({count} entries removed)")
    return count


def get_cache_stats():
    """Get cache statistics"""
    total = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = (_cache_stats["hits"] / total * 100) if total > 0 else 0
    
    return {
        "entries": len(_cache),
        "hits": _cache_stats["hits"],
        "misses": _cache_stats["misses"],
        "hit_rate": f"{hit_rate:.1f}%"
    }


def cleanup_expired(ttl_minutes=60):
    """Remove expired entries from cache"""
    global _cache
    now = datetime.now()
    expired_keys = []
    
    for key, (data, cached_time) in _cache.items():
        age = now - cached_time
        if age > timedelta(minutes=ttl_minutes):
            expired_keys.append(key)
    
    for key in expired_keys:
        del _cache[key]
    
    if expired_keys:
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    return len(expired_keys)
