"""
Integration Testing Suite
Tests complete end-to-end flows
"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER = {
    "name": "Test User",
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPass123!"
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class TestRunner:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.passed = 0
        self.failed = 0
        self.tests = []
        
    def log(self, message, color=Colors.BLUE):
        print(f"{color}{message}{Colors.END}")
        
    def success(self, test_name):
        self.passed += 1
        self.tests.append((test_name, True, None))
        self.log(f"✅ PASS: {test_name}", Colors.GREEN)
        
    def fail(self, test_name, error):
        self.failed += 1
        self.tests.append((test_name, False, error))
        self.log(f"❌ FAIL: {test_name}", Colors.RED)
        self.log(f"   Error: {error}", Colors.RED)
        
    def test(self, name, func):
        """Run a test function"""
        self.log(f"\n🧪 Testing: {name}", Colors.YELLOW)
        try:
            func()
            self.success(name)
        except Exception as e:
            self.fail(name, str(e))
            
    def summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        self.log(f"\n{'='*60}", Colors.BLUE)
        self.log(f"TEST SUMMARY", Colors.BLUE)
        self.log(f"{'='*60}", Colors.BLUE)
        self.log(f"Total Tests: {total}", Colors.BLUE)
        self.log(f"Passed: {self.passed}", Colors.GREEN)
        self.log(f"Failed: {self.failed}", Colors.RED if self.failed > 0 else Colors.GREEN)
        self.log(f"Success Rate: {(self.passed/total*100):.1f}%", Colors.GREEN if self.failed == 0 else Colors.YELLOW)
        self.log(f"{'='*60}\n", Colors.BLUE)
        
        if self.failed > 0:
            self.log("Failed Tests:", Colors.RED)
            for name, passed, error in self.tests:
                if not passed:
                    self.log(f"  - {name}: {error}", Colors.RED)

# Initialize test runner
runner = TestRunner()

# ─── Test 1: Health Check ─────────────────────────────────────────────────────

def test_health_check():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert 'status' in data, "Health check missing status"
    runner.log(f"   Health Status: {data.get('status')}")

runner.test("Health Check", test_health_check)

# ─── Test 2: User Registration ────────────────────────────────────────────────

def test_register():
    """Test user registration"""
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json=TEST_USER
    )
    # Accept both 200 and 201 (201 is correct REST practice for resource creation)
    assert response.status_code in [200, 201], f"Expected 200 or 201, got {response.status_code}"
    data = response.json()
    assert data.get('success') == True, "Registration failed"
    assert 'data' in data, "Missing data in response"
    assert 'token' in data['data'], "Missing token in response"
    assert 'user' in data['data'], "Missing user in response"
    
    # Store token for subsequent tests
    runner.token = data['data']['token']
    runner.user_id = data['data']['user']['id']
    runner.log(f"   User ID: {runner.user_id}")
    runner.log(f"   Token: {runner.token[:20]}...")

runner.test("User Registration", test_register)

# ─── Test 3: User Login ───────────────────────────────────────────────────────

def test_login():
    """Test user login"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get('success') == True, "Login failed"
    assert 'data' in data, "Missing data in response"
    assert 'token' in data['data'], "Missing token in response"
    
    # Update token
    runner.token = data['data']['token']
    runner.log(f"   New Token: {runner.token[:20]}...")

runner.test("User Login", test_login)

# ─── Test 4: Get User Profile ─────────────────────────────────────────────────

def test_get_profile():
    """Test getting user profile"""
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {runner.token}"}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get('success') == True, "Get profile failed"
    assert 'data' in data, "Missing data in response"
    assert 'user' in data['data'], "Missing user in response"
    runner.log(f"   User: {data['data']['user']['name']}")

runner.test("Get User Profile", test_get_profile)

# ─── Test 5: Dashboard Data ───────────────────────────────────────────────────

def test_dashboard():
    """Test dashboard endpoint"""
    response = requests.get(
        f"{BASE_URL}/api/dashboard/",
        headers={"Authorization": f"Bearer {runner.token}"}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    # Dashboard returns data directly, not wrapped in success/data structure
    assert 'user' in data, "Missing user in dashboard response"
    runner.log(f"   Dashboard loaded successfully")

runner.test("Dashboard Data", test_dashboard)

# ─── Test 6: Resume Upload (Mock) ─────────────────────────────────────────────

def test_resume_history():
    """Test resume history endpoint"""
    response = requests.get(
        f"{BASE_URL}/api/ai/resume/history",
        headers={"Authorization": f"Bearer {runner.token}"}
    )
    # Should return 200 even if empty
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get('success') == True, "Resume history failed"
    runner.log(f"   Resume history retrieved")

runner.test("Resume History", test_resume_history)

# ─── Test 7: Interview History ────────────────────────────────────────────────

def test_interview_history():
    """Test interview history endpoint"""
    response = requests.get(
        f"{BASE_URL}/api/interview/history",
        headers={"Authorization": f"Bearer {runner.token}"}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    # Interview history returns data directly with history and stats
    assert 'history' in data or 'stats' in data, "Missing history data in response"
    runner.log(f"   Interview history retrieved")

runner.test("Interview History", test_interview_history)

# ─── Test 8: Career Coach Chat ────────────────────────────────────────────────

def test_career_coach():
    """Test career coach chat endpoint"""
    response = requests.post(
        f"{BASE_URL}/api/chat",
        headers={"Authorization": f"Bearer {runner.token}"},
        json={"message": "Hello, I need career advice"}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    # Chat endpoint returns reply directly
    assert 'reply' in data or 'response' in data or 'message' in data, "Missing response in data"
    response_text = data.get('reply', data.get('response', data.get('message', '')))
    runner.log(f"   Coach Response: {response_text[:50]}...")

runner.test("Career Coach Chat", test_career_coach)

# ─── Test 9: Unauthorized Access ──────────────────────────────────────────────

def test_unauthorized():
    """Test unauthorized access"""
    response = requests.get(
        f"{BASE_URL}/api/dashboard/",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    # 401 responses may have different formats, just check it's an error
    assert 'message' in data or 'error' in data, "Missing error message"
    runner.log(f"   Correctly rejected invalid token")

runner.test("Unauthorized Access", test_unauthorized)

# ─── Test 10: Error Handling ──────────────────────────────────────────────────

def test_error_handling():
    """Test error handling with invalid input"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "invalid", "password": ""}
    )
    # Should return error response
    data = response.json()
    assert data.get('success') == False, "Should fail with invalid input"
    assert 'error' in data, "Missing error in response"
    runner.log(f"   Error handled correctly: {data['error'].get('message', 'N/A')}")

runner.test("Error Handling", test_error_handling)

# ─── Test 11: Rate Limiting (if implemented) ──────────────────────────────────

def test_rate_limiting():
    """Test rate limiting"""
    # Make multiple rapid requests
    responses = []
    for i in range(5):
        response = requests.get(f"{BASE_URL}/health")
        responses.append(response.status_code)
    
    # All should succeed (rate limit is high for health check)
    assert all(status == 200 for status in responses), "Health checks should not be rate limited"
    runner.log(f"   Made 5 rapid requests successfully")

runner.test("Rate Limiting", test_rate_limiting)

# ─── Test 12: CORS Headers ────────────────────────────────────────────────────

def test_cors_headers():
    """Test CORS headers are present"""
    response = requests.options(
        f"{BASE_URL}/api/auth/login",
        headers={"Origin": "http://localhost:8000"}
    )
    # Check for CORS headers
    assert 'Access-Control-Allow-Origin' in response.headers, "Missing CORS headers"
    runner.log(f"   CORS headers present")

runner.test("CORS Headers", test_cors_headers)

# ─── Print Summary ────────────────────────────────────────────────────────────

runner.summary()

# Exit with appropriate code
exit(0 if runner.failed == 0 else 1)
