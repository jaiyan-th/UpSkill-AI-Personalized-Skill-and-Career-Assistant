"""
Custom Exception Classes for UpSkill AI Platform
Provides structured error handling with consistent error codes
"""


class UpSkillException(Exception):
    """Base exception for all UpSkill errors"""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


# ─── Authentication Errors ────────────────────────────────────────────────────
class AuthenticationError(UpSkillException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_FAILED", 401)


class InvalidCredentialsError(UpSkillException):
    """Raised when login credentials are invalid"""
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message, "INVALID_CREDENTIALS", 401)


class TokenExpiredError(UpSkillException):
    """Raised when JWT token has expired"""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, "TOKEN_EXPIRED", 401)


class TokenInvalidError(UpSkillException):
    """Raised when JWT token is invalid"""
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, "TOKEN_INVALID", 401)


class UnauthorizedError(UpSkillException):
    """Raised when user lacks permission"""
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, "UNAUTHORIZED", 403)


# ─── Validation Errors ────────────────────────────────────────────────────────
class ValidationError(UpSkillException):
    """Raised when request validation fails"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR", 400)


class MissingFieldError(ValidationError):
    """Raised when required field is missing"""
    def __init__(self, field: str):
        super().__init__(f"Missing required field: {field}", field)
        self.code = "MISSING_FIELD"


class InvalidFieldError(ValidationError):
    """Raised when field value is invalid"""
    def __init__(self, field: str, reason: str = "Invalid value"):
        super().__init__(f"Invalid field '{field}': {reason}", field)
        self.code = "INVALID_FIELD"


# ─── Resource Errors ──────────────────────────────────────────────────────────
class ResourceNotFoundError(UpSkillException):
    """Raised when requested resource doesn't exist"""
    def __init__(self, resource: str, identifier: str = None):
        msg = f"{resource} not found"
        if identifier:
            msg += f": {identifier}"
        super().__init__(msg, "RESOURCE_NOT_FOUND", 404)


class ResourceExistsError(UpSkillException):
    """Raised when resource already exists"""
    def __init__(self, resource: str, identifier: str = None):
        msg = f"{resource} already exists"
        if identifier:
            msg += f": {identifier}"
        super().__init__(msg, "RESOURCE_EXISTS", 409)


# ─── External Service Errors ──────────────────────────────────────────────────
class ExternalServiceError(UpSkillException):
    """Raised when external service (LLM, API) fails"""
    def __init__(self, service: str, message: str = "Service unavailable"):
        super().__init__(f"{service}: {message}", "EXTERNAL_SERVICE_ERROR", 503)


class LLMError(ExternalServiceError):
    """Raised when LLM API fails"""
    def __init__(self, message: str = "LLM service error"):
        super().__init__("LLM", message)


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out"""
    def __init__(self, message: str = "LLM request timed out"):
        super().__init__(message)
        self.code = "LLM_TIMEOUT"


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded"""
    def __init__(self, message: str = "LLM rate limit exceeded"):
        super().__init__(message)
        self.code = "LLM_RATE_LIMIT"


# ─── Database Errors ──────────────────────────────────────────────────────────
class DatabaseError(UpSkillException):
    """Raised when database operation fails"""
    def __init__(self, message: str = "Database error occurred"):
        super().__init__(message, "DATABASE_ERROR", 500)


# ─── Business Logic Errors ────────────────────────────────────────────────────
class BusinessLogicError(UpSkillException):
    """Raised when business rule is violated"""
    def __init__(self, message: str):
        super().__init__(message, "BUSINESS_LOGIC_ERROR", 422)


class InterviewSessionError(BusinessLogicError):
    """Raised when interview session operation fails"""
    def __init__(self, message: str):
        super().__init__(message)
        self.code = "INTERVIEW_SESSION_ERROR"


class ResumeProcessingError(BusinessLogicError):
    """Raised when resume processing fails"""
    def __init__(self, message: str):
        super().__init__(message)
        self.code = "RESUME_PROCESSING_ERROR"
