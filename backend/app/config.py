import os


def _get_db_path():
    """
    Use /tmp on Vercel (read-only filesystem), local path otherwise.
    Vercel sets the VERCEL environment variable automatically.
    """
    default_name = os.getenv("DATABASE_PATH", "skilliq.db")
    if os.getenv("VERCEL"):
        return os.path.join("/tmp", os.path.basename(default_name))
    return default_name


class Config:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "supersecretkey_change_in_production")
    DATABASE_PATH = _get_db_path()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
