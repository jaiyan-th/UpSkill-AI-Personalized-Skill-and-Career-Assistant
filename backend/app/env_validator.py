"""
Environment Variable Validator
Ensures all required configuration is present before app starts
"""

import os
import sys


REQUIRED_ENV_VARS = [
    'SECRET_KEY',
]

OPTIONAL_ENV_VARS = [
    'DATABASE_URL',
    'FLASK_ENV',
    'ALLOWED_ORIGINS',
]

LLM_API_KEYS = [
    'GROQ_API_KEY',
    'OPENAI_API_KEY',
    'ANTHROPIC_API_KEY',
]


def validate_environment():
    """
    Validate required environment variables
    Exits with error if validation fails
    """
    print("\n" + "=" * 60)
    print("🔍 Validating Environment Configuration")
    print("=" * 60)
    
    missing = []
    warnings = []
    
    # Check required variables
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            print(f"✓ {var}: {'*' * min(len(value), 20)}")
    
    # Check at least one LLM API key
    llm_keys_found = []
    for key in LLM_API_KEYS:
        if os.getenv(key):
            llm_keys_found.append(key)
            print(f"✓ {key}: {'*' * 20}")
    
    if not llm_keys_found:
        missing.append("At least one LLM API key (GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)")
    
    # Check optional variables
    for var in OPTIONAL_ENV_VARS:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value}")
        else:
            warnings.append(var)
    
    # Report results
    print("=" * 60)
    
    if missing:
        print("\n❌ VALIDATION FAILED")
        print("\nMissing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        print("=" * 60)
        sys.exit(1)
    
    if warnings:
        print("\n⚠️  Optional variables not set:")
        for var in warnings:
            print(f"  - {var}")
    
    print("\n✅ Environment validation passed")
    print("=" * 60 + "\n")


def get_config_summary():
    """Return a summary of current configuration"""
    return {
        "flask_env": os.getenv("FLASK_ENV", "development"),
        "database": os.getenv("DATABASE_URL", "sqlite:///skilliq.db"),
        "llm_provider": "groq" if os.getenv("GROQ_API_KEY") else "openai" if os.getenv("OPENAI_API_KEY") else "anthropic",
        "cors_origins": os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(","),
    }
