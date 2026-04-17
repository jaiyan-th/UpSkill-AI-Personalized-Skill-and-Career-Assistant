"""
TASK 3: PERFORMANCE TESTING
Measure API response times and system performance
"""
import requests
import time
import json

BASE_URL = "http://localhost:5000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(message, color=Colors.BLUE):
    print(f"{color}{message}{Colors.END}")

def measure_time(func):
    """Decorator to measure execution time"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        return result, (end - start) * 1000  # Return result and time in ms
    return wrapper

log("=" * 70, Colors.BLUE)
log("TASK 3: PERFORMANCE TESTING", Colors.BLUE)
log("Measuring API response times and system performance", Colors.BLUE)
log("=" * 70, Colors.BLUE)

# Setup: Create test user
TEST_USER = {
    "name": "Perf Test User",
    "email": f"perf_test_{int(time.time())}@example.com",
    "password": "TestPass123!"
}

results = []

# Test 1: Health Check
log("\n1. Health Check Performance", Colors.YELLOW)
times = []
for i in range(5):
    start = time.time()
    response = requests.get(f"{BASE_URL}/health")
    end = time.time()
    times.append((end - start) * 1000)

avg_time = sum(times) / len(times)
log(f"   Average: {avg_time:.2f}ms", Colors.GREEN if avg_time < 100 else Colors.YELLOW)
log(f"   Min: {min(times):.2f}ms, Max: {max(times):.2f}ms", Colors.BLUE)
results.append(("Health Check", avg_time, 100))

# Test 2: Registration
log("\n2. User Registration Performance", Colors.YELLOW)
start = time.time()
response = requests.post(f"{BASE_URL}/api/auth/register", json=TEST_USER)
end = time.time()
reg_time = (end - start) * 1000
token = response.json().get('data', {}).get('token', '')
log(f"   Time: {reg_time:.2f}ms", Colors.GREEN if reg_time < 500 else Colors.YELLOW)
results.append(("Registration", reg_time, 500))

# Test 3: Login
log("\n3. User Login Performance", Colors.YELLOW)
times = []
for i in range(3):
    start = time.time()
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    end = time.time()
    times.append((end - start) * 1000)

avg_time = sum(times) / len(times)
log(f"   Average: {avg_time:.2f}ms", Colors.GREEN if avg_time < 500 else Colors.YELLOW)
results.append(("Login", avg_time, 500))

# Test 4: Dashboard
log("\n4. Dashboard Load Performance", Colors.YELLOW)
times = []
for i in range(3):
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/api/dashboard/",
        headers={"Authorization": f"Bearer {token}"}
    )
    end = time.time()
    times.append((end - start) * 1000)

avg_time = sum(times) / len(times)
log(f"   Average: {avg_time:.2f}ms", Colors.GREEN if avg_time < 1000 else Colors.YELLOW)
results.append(("Dashboard", avg_time, 1000))

# Test 5: Profile
log("\n5. Profile Retrieval Performance", Colors.YELLOW)
times = []
for i in range(3):
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    end = time.time()
    times.append((end - start) * 1000)

avg_time = sum(times) / len(times)
log(f"   Average: {avg_time:.2f}ms", Colors.GREEN if avg_time < 500 else Colors.YELLOW)
results.append(("Profile", avg_time, 500))

# Test 6: Resume History
log("\n6. Resume History Performance", Colors.YELLOW)
start = time.time()
response = requests.get(
    f"{BASE_URL}/api/ai/resume/history",
    headers={"Authorization": f"Bearer {token}"}
)
end = time.time()
history_time = (end - start) * 1000
log(f"   Time: {history_time:.2f}ms", Colors.GREEN if history_time < 500 else Colors.YELLOW)
results.append(("Resume History", history_time, 500))

# Test 7: Interview History
log("\n7. Interview History Performance", Colors.YELLOW)
start = time.time()
response = requests.get(
    f"{BASE_URL}/api/interview/history",
    headers={"Authorization": f"Bearer {token}"}
)
end = time.time()
interview_time = (end - start) * 1000
log(f"   Time: {interview_time:.2f}ms", Colors.GREEN if interview_time < 500 else Colors.YELLOW)
results.append(("Interview History", interview_time, 500))

# Test 8: Chat (LLM call)
log("\n8. Chat Response Performance (LLM)", Colors.YELLOW)
start = time.time()
response = requests.post(
    f"{BASE_URL}/api/chat",
    headers={"Authorization": f"Bearer {token}"},
    json={"message": "What is Python?"}
)
end = time.time()
chat_time = (end - start) * 1000
log(f"   Time: {chat_time:.2f}ms", Colors.GREEN if chat_time < 5000 else Colors.YELLOW)
results.append(("Chat (LLM)", chat_time, 5000))

# Summary
log("\n" + "=" * 70, Colors.BLUE)
log("PERFORMANCE SUMMARY", Colors.BLUE)
log("=" * 70, Colors.BLUE)

log("\n{:<25} {:>15} {:>15} {:>10}".format("Endpoint", "Avg Time", "Target", "Status"), Colors.BLUE)
log("-" * 70, Colors.BLUE)

all_pass = True
for name, avg_time, target in results:
    status = "✅ PASS" if avg_time < target else "⚠️ SLOW"
    color = Colors.GREEN if avg_time < target else Colors.YELLOW
    log("{:<25} {:>12.2f}ms {:>12}ms {:>10}".format(name, avg_time, target, status), color)
    if avg_time >= target:
        all_pass = False

log("\n" + "=" * 70, Colors.BLUE)

if all_pass:
    log("✅ ALL PERFORMANCE TARGETS MET", Colors.GREEN)
else:
    log("⚠️ SOME ENDPOINTS SLOWER THAN TARGET (Still acceptable)", Colors.YELLOW)

log("\nKEY METRICS:", Colors.YELLOW)
log(f"  • Fastest endpoint: {min(results, key=lambda x: x[1])[0]} ({min(results, key=lambda x: x[1])[1]:.2f}ms)", Colors.GREEN)
log(f"  • Slowest endpoint: {max(results, key=lambda x: x[1])[0]} ({max(results, key=lambda x: x[1])[1]:.2f}ms)", Colors.YELLOW)
log(f"  • Average response time: {sum(r[1] for r in results) / len(results):.2f}ms", Colors.BLUE)

log("\n✅ PERFORMANCE TESTING COMPLETE", Colors.GREEN)
