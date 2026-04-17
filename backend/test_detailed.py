"""
Detailed Testing - Investigate failures
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"
TEST_USER = {
    "name": "QA Test User",
    "email": f"qa_test_{int(time.time())}@example.com",
    "password": "TestPass123!"
}

print("=" * 60)
print("DETAILED TESTING - INVESTIGATING FAILURES")
print("=" * 60)

# Test 1: Registration (expecting 201 but test expects 200)
print("\n1. Testing Registration...")
response = requests.post(f"{BASE_URL}/api/auth/register", json=TEST_USER)
print(f"   Status: {response.status_code}")
print(f"   Response: {json.dumps(response.json(), indent=2)}")

# Store token
token = response.json().get('data', {}).get('token', '')

# Test 2: Dashboard
print("\n2. Testing Dashboard...")
response = requests.get(
    f"{BASE_URL}/api/dashboard/",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {json.dumps(response.json(), indent=2)}")

# Test 3: Interview History
print("\n3. Testing Interview History...")
response = requests.get(
    f"{BASE_URL}/api/interview/history",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {json.dumps(response.json(), indent=2)}")

# Test 4: Career Coach Chat
print("\n4. Testing Career Coach Chat...")
response = requests.post(
    f"{BASE_URL}/api/ai/chat/message",
    headers={"Authorization": f"Bearer {token}"},
    json={"message": "Hello"}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:500]}")

# Test 5: Unauthorized Access
print("\n5. Testing Unauthorized Access...")
response = requests.get(
    f"{BASE_URL}/api/dashboard/",
    headers={"Authorization": "Bearer invalid_token"}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {json.dumps(response.json(), indent=2)}")

print("\n" + "=" * 60)
