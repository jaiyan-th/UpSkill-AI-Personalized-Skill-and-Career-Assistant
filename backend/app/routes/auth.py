from flask import Blueprint, request
from app.database import get_db
from app.auth_utils import hash_password, verify_password, create_token, require_auth
from app.error_handlers import success_response, error_response
from app.exceptions import (
    InvalidCredentialsError,
    ResourceExistsError,
    ResourceNotFoundError,
    DatabaseError
)
from app.validators import validate_request, AUTH_LOGIN_SCHEMA, AUTH_REGISTER_SCHEMA
from app.services.email_service import get_email_service
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
@validate_request(AUTH_REGISTER_SCHEMA)
def register():
    """
    Register a new user
    
    Request Body:
        - name: string (required, 2-100 chars)
        - email: string (required, valid email)
        - password: string (required, min 8 chars)
        - role: string (optional, default: "student")
    
    Returns:
        201: { success: true, data: { user, token }, message }
        409: { success: false, error: { code, message } }
    """
    data = request.validated_data
    role = request.get_json().get("role", "student")
    
    try:
        db = get_db()
        
        # Check if email already exists
        existing = db.execute("SELECT id FROM users WHERE email = ?", [data["email"]]).fetchone()
        if existing:
            raise ResourceExistsError("User", data["email"])
        
        # Create user
        hashed = hash_password(data["password"])
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            [data["name"], data["email"], hashed, role],
        )
        db.commit()
        
        # Build response
        user = {
            "id": cur.lastrowid,
            "name": data["name"],
            "email": data["email"],
            "role": role
        }
        token = create_token({
            "id": user["id"],
            "email": data["email"],
            "role": role,
            "name": data["name"]
        })
        
        # Send welcome email (non-blocking)
        try:
            email_service = get_email_service()
            email_service.send_welcome_email(data["name"], data["email"])
        except Exception as e:
            # Log error but don't fail registration
            import logging
            logging.getLogger(__name__).error(f"Failed to send welcome email: {str(e)}")
        
        return success_response(
            data={"user": user, "token": token},
            message="Registration successful",
            status_code=201
        )
        
    except (ResourceExistsError, DatabaseError):
        raise
    except Exception as e:
        raise DatabaseError(f"Registration failed: {str(e)}")


@auth_bp.post("/login")
@validate_request(AUTH_LOGIN_SCHEMA)
def login():
    """
    Authenticate user and return JWT token
    
    Request Body:
        - email: string (required, valid email)
        - password: string (required)
    
    Returns:
        200: { success: true, data: { user, token }, message }
        401: { success: false, error: { code: "INVALID_CREDENTIALS", message } }
    
    Example Success Response:
        {
            "success": true,
            "data": {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "user": {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "role": "student"
                }
            },
            "message": "Login successful"
        }
    """
    data = request.validated_data
    
    try:
        db = get_db()
        row = db.execute("SELECT * FROM users WHERE email = ?", [data["email"]]).fetchone()
        
        # Verify credentials
        if not row or not verify_password(data["password"], row["password_hash"]):
            raise InvalidCredentialsError()
        
        # Build response
        user = {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "role": row["role"]
        }
        token = create_token({
            "id": user["id"],
            "email": data["email"],
            "role": user["role"],
            "name": user["name"]
        })
        
        # Send login alert email (non-blocking)
        try:
            email_service = get_email_service()
            email_service.send_login_alert(user["name"], user["email"], datetime.now())
        except Exception as e:
            # Log error but don't fail login
            import logging
            logging.getLogger(__name__).error(f"Failed to send login alert: {str(e)}")
        
        return success_response(
            data={"token": token, "user": user},
            message="Login successful"
        )
        
    except InvalidCredentialsError:
        raise
    except Exception as e:
        raise DatabaseError(f"Login failed: {str(e)}")


@auth_bp.get("/me")
@require_auth
def me():
    """
    Get current authenticated user profile
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        200: { success: true, data: { user } }
        404: { success: false, error: { code: "RESOURCE_NOT_FOUND", message } }
    """
    try:
        db = get_db()
        row = db.execute(
            "SELECT id, name, email, role FROM users WHERE id = ?",
            [request.user["id"]]
        ).fetchone()
        
        if not row:
            raise ResourceNotFoundError("User", str(request.user["id"]))
        
        user = {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "role": row["role"]
        }
        
        return success_response(data={"user": user})
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        raise DatabaseError(f"Failed to fetch user: {str(e)}")
