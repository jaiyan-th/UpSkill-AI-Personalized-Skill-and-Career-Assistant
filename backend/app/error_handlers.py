"""
Global Error Handlers and Response Utilities
Provides consistent API response format across all endpoints
"""

from flask import jsonify
from typing import Any, Dict, Optional
import traceback
import logging

from .exceptions import UpSkillException

# Configure logging
logger = logging.getLogger(__name__)


# ─── Response Utilities ───────────────────────────────────────────────────────
def success_response(
    data: Any = None,
    message: str = None,
    status_code: int = 200
) -> tuple:
    """
    Create standardized success response
    
    Args:
        data: Response payload (dict, list, or any JSON-serializable)
        message: Optional success message
        status_code: HTTP status code (default: 200)
    
    Returns:
        Tuple of (response_dict, status_code)
    
    Example:
        return success_response({"user": user_data}, "Login successful")
    """
    response = {
        "success": True,
        "data": data if data is not None else {}
    }
    
    if message:
        response["message"] = message
    
    return jsonify(response), status_code


def error_response(
    message: str,
    code: str = "ERROR",
    status_code: int = 400,
    details: Dict = None
) -> tuple:
    """
    Create standardized error response
    
    Args:
        message: Human-readable error message
        code: Machine-readable error code (e.g., "INVALID_CREDENTIALS")
        status_code: HTTP status code (default: 400)
        details: Optional additional error details
    
    Returns:
        Tuple of (response_dict, status_code)
    
    Example:
        return error_response("Invalid email format", "VALIDATION_ERROR", 400)
    """
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return jsonify(response), status_code


# ─── Global Error Handlers ────────────────────────────────────────────────────
def register_error_handlers(app):
    """
    Register global error handlers with Flask app
    Call this in create_app() after app initialization
    """
    
    @app.errorhandler(UpSkillException)
    def handle_upskill_exception(error: UpSkillException):
        """Handle all custom UpSkill exceptions"""
        logger.warning(f"UpSkill Exception: {error.code} - {error.message}")
        return error_response(
            message=error.message,
            code=error.code,
            status_code=error.status_code
        )
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request"""
        return error_response(
            message="Bad request",
            code="BAD_REQUEST",
            status_code=400
        )
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found"""
        return error_response(
            message="Resource not found",
            code="NOT_FOUND",
            status_code=404
        )
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed"""
        return error_response(
            message="Method not allowed",
            code="METHOD_NOT_ALLOWED",
            status_code=405
        )
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server Error"""
        logger.error(f"Internal Server Error: {str(error)}")
        logger.error(traceback.format_exc())
        
        # Don't expose internal error details in production
        return error_response(
            message="An internal error occurred",
            code="INTERNAL_ERROR",
            status_code=500
        )
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Catch-all for unexpected exceptions"""
        logger.error(f"Unexpected Error: {str(error)}")
        logger.error(traceback.format_exc())
        
        return error_response(
            message="An unexpected error occurred",
            code="UNEXPECTED_ERROR",
            status_code=500
        )
    
    logger.info("Global error handlers registered")
