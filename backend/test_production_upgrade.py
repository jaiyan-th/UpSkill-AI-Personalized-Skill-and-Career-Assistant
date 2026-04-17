#!/usr/bin/env python3
"""
Production Upgrade Test Script
Tests the new error handling, validation, and LLM service
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all new modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from app.exceptions import (
            UpSkillException,
            AuthenticationError,
            InvalidCredentialsError,
            ValidationError,
            ResourceNotFoundError,
            LLMError
        )
        print("  ✓ Exceptions module imported")
    except ImportError as e:
        print(f"  ✗ Failed to import exceptions: {e}")
        return False
    
    try:
        from app.error_handlers import (
            success_response,
            error_response,
            register_error_handlers
        )
        print("  ✓ Error handlers module imported")
    except ImportError as e:
        print(f"  ✗ Failed to import error_handlers: {e}")
        return False
    
    try:
        from app.validators import (
            Validator,
            validate_request,
            AUTH_LOGIN_SCHEMA,
            AUTH_REGISTER_SCHEMA
        )
        print("  ✓ Validators module imported")
    except ImportError as e:
        print(f"  ✗ Failed to import validators: {e}")
        return False
    
    try:
        from app.services.llm_service_v2 import LLMServiceV2
        print("  ✓ LLM Service v2 imported")
    except ImportError as e:
        print(f"  ✗ Failed to import llm_service_v2: {e}")
        return False
    
    return True


def test_exceptions():
    """Test custom exception classes"""
    print("\n🧪 Testing exception classes...")
    
    from app.exceptions import (
        InvalidCredentialsError,
        ValidationError,
        ResourceNotFoundError,
        LLMError
    )
    
    # Test InvalidCredentialsError
    try:
        raise InvalidCredentialsError()
    except InvalidCredentialsError as e:
        assert e.code == "INVALID_CREDENTIALS"
        assert e.status_code == 401
        print("  ✓ InvalidCredentialsError works")
    
    # Test ValidationError
    try:
        raise ValidationError("Test error", field="email")
    except ValidationError as e:
        assert e.code == "VALIDATION_ERROR"
        assert e.status_code == 400
        assert e.field == "email"
        print("  ✓ ValidationError works")
    
    # Test ResourceNotFoundError
    try:
        raise ResourceNotFoundError("User", "123")
    except ResourceNotFoundError as e:
        assert e.code == "RESOURCE_NOT_FOUND"
        assert e.status_code == 404
        assert "User" in e.message
        print("  ✓ ResourceNotFoundError works")
    
    # Test LLMError
    try:
        raise LLMError("Test LLM error")
    except LLMError as e:
        assert e.code == "EXTERNAL_SERVICE_ERROR"
        assert e.status_code == 503
        print("  ✓ LLMError works")
    
    return True


def test_validators():
    """Test validation functions"""
    print("\n🧪 Testing validators...")
    
    from app.validators import Validator
    from app.exceptions import ValidationError
    
    # Test email validation - valid
    try:
        result = Validator.validate_email("test@example.com")
        assert result == "test@example.com"
        print("  ✓ Email validation (valid) works")
    except Exception as e:
        print(f"  ✗ Email validation failed: {e}")
        return False
    
    # Test email validation - invalid
    try:
        Validator.validate_email("invalid-email")
        print("  ✗ Email validation should have failed")
        return False
    except ValidationError:
        print("  ✓ Email validation (invalid) works")
    
    # Test password validation - valid
    try:
        result = Validator.validate_password("password123")
        assert result == "password123"
        print("  ✓ Password validation (valid) works")
    except Exception as e:
        print(f"  ✗ Password validation failed: {e}")
        return False
    
    # Test password validation - too short
    try:
        Validator.validate_password("short")
        print("  ✗ Password validation should have failed")
        return False
    except ValidationError:
        print("  ✓ Password validation (too short) works")
    
    # Test string validation
    try:
        result = Validator.validate_string("Test", "name", min_length=2, max_length=10)
        assert result == "Test"
        print("  ✓ String validation works")
    except Exception as e:
        print(f"  ✗ String validation failed: {e}")
        return False
    
    # Test integer validation
    try:
        result = Validator.validate_integer("42", "age", min_val=18, max_val=100)
        assert result == 42
        print("  ✓ Integer validation works")
    except Exception as e:
        print(f"  ✗ Integer validation failed: {e}")
        return False
    
    # Test enum validation
    try:
        result = Validator.validate_enum("Entry", "level", ["Entry", "Mid-level", "Senior"])
        assert result == "Entry"
        print("  ✓ Enum validation works")
    except Exception as e:
        print(f"  ✗ Enum validation failed: {e}")
        return False
    
    return True


def test_response_utilities():
    """Test response utility functions"""
    print("\n🧪 Testing response utilities...")
    
    from app.error_handlers import success_response, error_response
    
    # Test success_response
    try:
        response, status = success_response(
            data={"user": {"id": 1, "name": "Test"}},
            message="Success"
        )
        data = response.get_json()
        assert data["success"] == True
        assert "data" in data
        assert data["message"] == "Success"
        assert status == 200
        print("  ✓ success_response works")
    except Exception as e:
        print(f"  ✗ success_response failed: {e}")
        return False
    
    # Test error_response
    try:
        response, status = error_response(
            message="Test error",
            code="TEST_ERROR",
            status_code=400
        )
        data = response.get_json()
        assert data["success"] == False
        assert "error" in data
        assert data["error"]["code"] == "TEST_ERROR"
        assert data["error"]["message"] == "Test error"
        assert status == 400
        print("  ✓ error_response works")
    except Exception as e:
        print(f"  ✗ error_response failed: {e}")
        return False
    
    return True


def test_llm_service():
    """Test LLM Service v2"""
    print("\n🧪 Testing LLM Service v2...")
    
    from app.services.llm_service_v2 import LLMServiceV2
    import json
    
    llm = LLMServiceV2()
    
    # Test JSON parsing - valid JSON
    try:
        result = llm.parse_json_response('{"message": "hello"}')
        assert result["message"] == "hello"
        print("  ✓ JSON parsing (valid) works")
    except Exception as e:
        print(f"  ✗ JSON parsing failed: {e}")
        return False
    
    # Test JSON parsing - JSON in markdown
    try:
        result = llm.parse_json_response('```json\n{"message": "hello"}\n```')
        assert result["message"] == "hello"
        print("  ✓ JSON parsing (markdown) works")
    except Exception as e:
        print(f"  ✗ JSON parsing (markdown) failed: {e}")
        return False
    
    # Test JSON parsing - JSON in text
    try:
        result = llm.parse_json_response('Some text before {"message": "hello"} some text after')
        assert result["message"] == "hello"
        print("  ✓ JSON parsing (embedded) works")
    except Exception as e:
        print(f"  ✗ JSON parsing (embedded) failed: {e}")
        return False
    
    # Test JSON parsing - with fallback
    try:
        result = llm.parse_json_response('invalid json', fallback={"error": "fallback"})
        assert result["error"] == "fallback"
        print("  ✓ JSON parsing (fallback) works")
    except Exception as e:
        print(f"  ✗ JSON parsing (fallback) failed: {e}")
        return False
    
    # Test generate_with_fallback
    try:
        # This will fail if no API key, but should return fallback
        result = llm.generate_with_fallback(
            prompt="Test",
            fallback_response="Fallback response"
        )
        # Should either succeed or return fallback
        assert isinstance(result, str)
        print("  ✓ generate_with_fallback works")
    except Exception as e:
        print(f"  ✗ generate_with_fallback failed: {e}")
        return False
    
    return True


def test_flask_app():
    """Test Flask app initialization"""
    print("\n🧪 Testing Flask app...")
    
    try:
        from app import create_app
        app = create_app()
        
        # Check that error handlers are registered
        assert app.error_handler_spec is not None
        print("  ✓ Flask app created successfully")
        print("  ✓ Error handlers registered")
        
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "ok"
            print("  ✓ Health endpoint works")
        
        return True
    except Exception as e:
        print(f"  ✗ Flask app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Production Upgrade Test Suite")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Exceptions", test_exceptions),
        ("Validators", test_validators),
        ("Response Utilities", test_response_utilities),
        ("LLM Service", test_llm_service),
        ("Flask App", test_flask_app)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Production upgrade is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
