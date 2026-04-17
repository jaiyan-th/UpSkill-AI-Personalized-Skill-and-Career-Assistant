"""
Test script for email notification system
Tests all email types and validates configuration
"""

import os
import sys
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.email_service import get_email_service


def test_email_configuration():
    """Test 1: Verify email configuration"""
    print("\n" + "="*60)
    print("TEST 1: Email Configuration")
    print("="*60)
    
    email_service = get_email_service()
    
    print(f"✓ Email Host: {email_service.host}")
    print(f"✓ Email Port: {email_service.port}")
    print(f"✓ Email User: {email_service.user}")
    print(f"✓ Email Enabled: {email_service.enabled}")
    print(f"✓ From Name: {email_service.from_name}")
    
    if not email_service.enabled:
        print("\n⚠️  WARNING: Email is disabled. Set EMAIL_ENABLED=true in .env")
        return False
    
    if not email_service.user or not email_service.password:
        print("\n❌ ERROR: Email credentials not configured!")
        print("Please set EMAIL_USER and EMAIL_PASS in .env file")
        return False
    
    print("\n✅ Email configuration is valid!")
    return True


def test_welcome_email():
    """Test 2: Send welcome email"""
    print("\n" + "="*60)
    print("TEST 2: Welcome Email")
    print("="*60)
    
    email_service = get_email_service()
    
    test_email = input("Enter test email address: ").strip()
    if not test_email:
        print("❌ No email provided, skipping test")
        return False
    
    print(f"\n📧 Sending welcome email to {test_email}...")
    
    try:
        email_service.send_welcome_email("Test User", test_email)
        print("✅ Welcome email sent successfully!")
        print("   Check your inbox (and spam folder)")
        return True
    except Exception as e:
        print(f"❌ Failed to send welcome email: {str(e)}")
        return False


def test_login_alert():
    """Test 3: Send login alert email"""
    print("\n" + "="*60)
    print("TEST 3: Login Alert Email")
    print("="*60)
    
    email_service = get_email_service()
    
    test_email = input("Enter test email address: ").strip()
    if not test_email:
        print("❌ No email provided, skipping test")
        return False
    
    print(f"\n📧 Sending login alert to {test_email}...")
    
    try:
        email_service.send_login_alert("Test User", test_email, datetime.now())
        print("✅ Login alert sent successfully!")
        print("   Check your inbox (and spam folder)")
        return True
    except Exception as e:
        print(f"❌ Failed to send login alert: {str(e)}")
        return False


def test_verification_email():
    """Test 4: Send verification email"""
    print("\n" + "="*60)
    print("TEST 4: Email Verification")
    print("="*60)
    
    email_service = get_email_service()
    
    test_email = input("Enter test email address: ").strip()
    if not test_email:
        print("❌ No email provided, skipping test")
        return False
    
    print(f"\n📧 Sending verification email to {test_email}...")
    
    try:
        email_service.send_verification_email("Test User", test_email, "ABC123")
        print("✅ Verification email sent successfully!")
        print("   Check your inbox (and spam folder)")
        return True
    except Exception as e:
        print(f"❌ Failed to send verification email: {str(e)}")
        return False


def test_password_reset():
    """Test 5: Send password reset email"""
    print("\n" + "="*60)
    print("TEST 5: Password Reset Email")
    print("="*60)
    
    email_service = get_email_service()
    
    test_email = input("Enter test email address: ").strip()
    if not test_email:
        print("❌ No email provided, skipping test")
        return False
    
    print(f"\n📧 Sending password reset email to {test_email}...")
    
    try:
        email_service.send_password_reset_email("Test User", test_email, "XYZ789")
        print("✅ Password reset email sent successfully!")
        print("   Check your inbox (and spam folder)")
        return True
    except Exception as e:
        print(f"❌ Failed to send password reset email: {str(e)}")
        return False


def test_non_blocking():
    """Test 6: Verify non-blocking behavior"""
    print("\n" + "="*60)
    print("TEST 6: Non-Blocking Email Delivery")
    print("="*60)
    
    import time
    
    email_service = get_email_service()
    
    print("📧 Sending 3 emails simultaneously...")
    start_time = time.time()
    
    # Send 3 emails at once (should not block)
    email_service.send_email(
        "test@example.com",
        "Test 1",
        "<h1>Test Email 1</h1>",
        "Test Email 1"
    )
    email_service.send_email(
        "test@example.com",
        "Test 2",
        "<h1>Test Email 2</h1>",
        "Test Email 2"
    )
    email_service.send_email(
        "test@example.com",
        "Test 3",
        "<h1>Test Email 3</h1>",
        "Test Email 3"
    )
    
    elapsed = time.time() - start_time
    
    print(f"✅ All emails queued in {elapsed:.3f} seconds")
    
    if elapsed < 0.1:
        print("✅ Non-blocking behavior confirmed!")
        return True
    else:
        print("⚠️  Warning: Email sending may be blocking")
        return False


def test_error_handling():
    """Test 7: Error handling with invalid email"""
    print("\n" + "="*60)
    print("TEST 7: Error Handling")
    print("="*60)
    
    email_service = get_email_service()
    
    print("📧 Testing with invalid email address...")
    
    try:
        # This should not crash the application
        email_service.send_welcome_email("Test User", "invalid-email")
        print("✅ Error handled gracefully (no crash)")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def run_all_tests():
    """Run all email system tests"""
    print("\n" + "="*60)
    print("🚀 UPSKILL AI - EMAIL SYSTEM TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Configuration
    results.append(("Configuration", test_email_configuration()))
    
    if not results[0][1]:
        print("\n❌ Email not configured. Please update .env file first.")
        return
    
    # Ask if user wants to run email sending tests
    print("\n" + "="*60)
    response = input("\nRun email sending tests? (y/n): ").strip().lower()
    
    if response == 'y':
        results.append(("Welcome Email", test_welcome_email()))
        results.append(("Login Alert", test_login_alert()))
        results.append(("Verification Email", test_verification_email()))
        results.append(("Password Reset", test_password_reset()))
    
    # Always run these tests
    results.append(("Non-Blocking", test_non_blocking()))
    results.append(("Error Handling", test_error_handling()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Email system is ready.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
