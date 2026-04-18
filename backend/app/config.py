import os


def _get_db_path():
    """
    Get the database connection string.
    Expects SUPABASE_DB_URL or DATABASE_URL in environment variables.
    """
    url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if not url:
        # Fallback to local postgres if nothing provided, but warn
        url = "postgresql://postgres:postgres@localhost:5432/upskill"
    return url


class Config:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "supersecretkey_change_in_production")
    SUPABASE_DB_URL = _get_db_path()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
