"""
Request Validation Layer
Validates and sanitizes all incoming requests
"""

from functools import wraps
from flask import request
from .exceptions import ValidationError
import re


class Validator:
    """Base validator class"""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        if not email:
            raise ValidationError("Email is required", field="email")
        
        email = email.strip().lower()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format", field="email")
        
        return email
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength"""
        if not password:
            raise ValidationError("Password is required", field="password")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters", field="password")
        
        return password
    
    @staticmethod
    def validate_required(value, field_name: str):
        """Validate required field"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} is required", field=field_name)
        return value
    
    @staticmethod
    def validate_string(value, field_name: str, min_length: int = None, max_length: int = None):
        """Validate string field"""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string", field=field_name)
        
        value = value.strip()
        
        if min_length and len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters",
                field=field_name
            )
        
        if max_length and len(value) > max_length:
            raise ValidationError(
                f"{field_name} must not exceed {max_length} characters",
                field=field_name
            )
        
        return value
    
    @staticmethod
    def validate_integer(value, field_name: str, min_val: int = None, max_val: int = None):
        """Validate integer field"""
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be an integer", field=field_name)
        
        if min_val is not None and value < min_val:
            raise ValidationError(
                f"{field_name} must be at least {min_val}",
                field=field_name
            )
        
        if max_val is not None and value > max_val:
            raise ValidationError(
                f"{field_name} must not exceed {max_val}",
                field=field_name
            )
        
        return value
    
    @staticmethod
    def validate_enum(value, field_name: str, allowed_values: list):
        """Validate enum field"""
        if value not in allowed_values:
            raise ValidationError(
                f"{field_name} must be one of: {', '.join(allowed_values)}",
                field=field_name
            )
        return value
    
    @staticmethod
    def validate_file(file, field_name: str, allowed_extensions: list, max_size_mb: int = 5):
        """Validate uploaded file"""
        if not file:
            raise ValidationError(f"{field_name} is required", field=field_name)
        
        if not file.filename:
            raise ValidationError("File has no filename", field=field_name)
        
        # Check extension
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            raise ValidationError(
                f"File must be one of: {', '.join(allowed_extensions)}",
                field=field_name
            )
        
        # Check size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if size > max_size_bytes:
            raise ValidationError(
                f"File size must not exceed {max_size_mb}MB",
                field=field_name
            )
        
        return file


def validate_request(schema):
    """
    Decorator to validate request data against a schema
    
    Usage:
        @validate_request({
            "email": {"type": "email", "required": True},
            "name": {"type": "string", "required": True, "min_length": 2}
        })
        def my_route():
            data = request.validated_data
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json() if request.is_json else request.form.to_dict()
            validated = {}
            
            for field, rules in schema.items():
                value = data.get(field)
                
                # Check required
                if rules.get("required") and value is None:
                    raise ValidationError(f"{field} is required", field=field)
                
                # Skip validation if not required and not provided
                if value is None:
                    continue
                
                # Validate based on type
                field_type = rules.get("type", "string")
                
                if field_type == "email":
                    validated[field] = Validator.validate_email(value)
                
                elif field_type == "password":
                    validated[field] = Validator.validate_password(value)
                
                elif field_type == "string":
                    validated[field] = Validator.validate_string(
                        value, field,
                        min_length=rules.get("min_length"),
                        max_length=rules.get("max_length")
                    )
                
                elif field_type == "integer":
                    validated[field] = Validator.validate_integer(
                        value, field,
                        min_val=rules.get("min_val"),
                        max_val=rules.get("max_val")
                    )
                
                elif field_type == "enum":
                    validated[field] = Validator.validate_enum(
                        value, field,
                        allowed_values=rules.get("allowed_values", [])
                    )
                
                else:
                    validated[field] = value
            
            # Attach validated data to request
            request.validated_data = validated
            
            return f(*args, **kwargs)
        
        return wrapper
    return decorator


# Common validation schemas
AUTH_REGISTER_SCHEMA = {
    "name": {"type": "string", "required": True, "min_length": 2, "max_length": 100},
    "email": {"type": "email", "required": True},
    "password": {"type": "password", "required": True}
}

AUTH_LOGIN_SCHEMA = {
    "email": {"type": "email", "required": True},
    "password": {"type": "string", "required": True}
}

INTERVIEW_START_SCHEMA = {
    "role": {"type": "string", "required": True, "min_length": 2},
    "level": {"type": "enum", "required": True, "allowed_values": ["Entry", "Mid-level", "Senior"]}
}

SKILL_GAP_SCHEMA = {
    "role": {"type": "string", "required": True},
    "level": {"type": "enum", "required": True, "allowed_values": ["Entry", "Mid-level", "Senior"]}
}
