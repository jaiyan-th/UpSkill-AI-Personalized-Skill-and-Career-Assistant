import hashlib
import hmac
import os
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":")
        return hmac.compare_digest(
            hashlib.sha256((salt + password).encode()).hexdigest(), hashed
        )
    except Exception:
        return False


def create_token(payload: dict) -> str:
    # Token expires in 24 hours — forces re-login each day
    payload = {**payload, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": {"code": "UNAUTHORIZED", "message": "Authentication required"}}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            request.user = payload
            
            import inspect
            sig = inspect.signature(f)
            if 'current_user' in sig.parameters:
                return f(*args, current_user=payload, **kwargs)
            else:
                return f(*args, **kwargs)
                
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": {"code": "TOKEN_EXPIRED", "message": "Session expired. Please log in again."}}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "error": {"code": "TOKEN_INVALID", "message": "Invalid token. Please log in again."}}), 401
    return decorated
