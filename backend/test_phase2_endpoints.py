#!/usr/bin/env python3
"""
Phase 2 Endpoint Testing Script
Tests the new production-ready endpoints
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")


class EndpointTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.session_id = None
        
    def test_health(self):
        """Test health endpoint"""
        print("\n" + "="*60)
        print("Testing Health Endpoint")
        print("="*60)
        
        try:
            response = requests.get(f"{BASE_URL}/health")
            data = response.json()
            
            if response.status_code == 200 and data.get("status") == "ok":
                print_success("Health endpoint working")
                return True
            else:
                print_error(f"Health check failed: {data}")
                return False
        except Exception as e:
            print_error(f"Health check error: {e}")
            return False
    
    def test_auth(self):
        """Test authentication"""
        print("\n" + "="*60)
        print("Testing Authentication")
        print("="*60)
        
        # Test login
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "test@example.com", "password": "password123"}
            )
            data = response.json()
            
            if response.status_code == 200 and data.get("success"):
                self.token = data["data"]["token"]
                self.user_id = data["data"]["user"]["id"]
                print_success(f"Login successful (User ID: {self.user_id})")
                print_info(f"Response format: {json.dumps(data, indent=2)[:200]}...")
                return True
            else:
                print_warning("Login failed (user may not exist)")
                print_info("Try registering first or check credentials")
                return False
        except Exception as e:
            print_error(f"Login error: {e}")
            return False
    
    def test_resume_endpoints(self):
        """Test resume endpoints"""
        print("\n" + "="*60)
        print("Testing Resume Endpoints")
        print("="*60)
        
        if not self.token:
            print_warning("Skipping resume tests (not authenticated)")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test ATS optimization
        print("\n1. Testing ATS Optimization...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/ai/resume/ats-optimization",
                headers=headers,
                json={
                    "resume_text": "Software Engineer with 5 years of experience in Python, JavaScript, React, and Node.js. Built scalable web applications and APIs."
                }
            )
            data = response.json()
            
            if response.status_code == 200 and data.get("success"):
                print_success("ATS optimization endpoint working")
                print_info(f"ATS Score: {data['data'].get('ats_score', 'N/A')}")
                return True
            else:
                print_error(f"ATS optimization failed: {data}")
                return False
        except Exception as e:
            print_error(f"ATS optimization error: {e}")
            return False
    
    def test_interview_endpoints(self):
        """Test interview endpoints"""
        print("\n" + "="*60)
        print("Testing Interview Endpoints")
        print("="*60)
        
        if not self.token:
            print_warning("Skipping interview tests (not authenticated)")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test start interview
        print("\n1. Testing Start Interview...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/ai/interview/start",
                headers=headers,
                json={
                    "role": "Software Developer",
                    "level": "Mid-level"
                }
            )
            data = response.json()
            
            if response.status_code == 201 and data.get("success"):
                self.session_id = data["data"]["session_id"]
                print_success(f"Interview started (Session ID: {self.session_id})")
                print_info(f"First question: {data['data']['first_question'][:100]}...")
                
                # Test submit answer
                print("\n2. Testing Submit Answer...")
                response = requests.post(
                    f"{BASE_URL}/api/ai/interview/answer",
                    headers=headers,
                    json={
                        "session_id": self.session_id,
                        "answer": "I have 5 years of experience in software development, working with Python, JavaScript, and various frameworks. I've built scalable web applications and led small teams."
                    }
                )
                data = response.json()
                
                if response.status_code == 200 and data.get("success"):
                    print_success("Answer submitted successfully")
                    print_info(f"Evaluation score: {data['data']['evaluation']['score']}/10")
                    
                    # Test end interview
                    print("\n3. Testing End Interview...")
                    response = requests.post(
                        f"{BASE_URL}/api/ai/interview/end",
                        headers=headers,
                        json={"session_id": self.session_id}
                    )
                    data = response.json()
                    
                    if response.status_code == 200 and data.get("success"):
                        print_success("Interview ended successfully")
                        print_info(f"Overall score: {data['data']['evaluation']['overall_score']}/100")
                        return True
                    else:
                        print_error(f"End interview failed: {data}")
                        return False
                else:
                    print_error(f"Submit answer failed: {data}")
                    return False
            else:
                print_error(f"Start interview failed: {data}")
                return False
        except Exception as e:
            print_error(f"Interview test error: {e}")
            return False
    
    def test_skill_gap_endpoints(self):
        """Test skill gap endpoints"""
        print("\n" + "="*60)
        print("Testing Skill Gap Endpoints")
        print("="*60)
        
        if not self.token:
            print_warning("Skipping skill gap tests (not authenticated)")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test analyze gaps
        print("\n1. Testing Analyze Skill Gaps...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/ai/skills/analyze-gaps",
                headers=headers,
                json={
                    "current_skills": "Python, JavaScript, React, SQL",
                    "target_role": "Full Stack Developer",
                    "experience_level": "Mid-level"
                }
            )
            data = response.json()
            
            if response.status_code == 200 and data.get("success"):
                print_success("Skill gap analysis working")
                print_info(f"Readiness score: {data['data'].get('readiness_score', 'N/A')}/100")
                
                # Test learning path
                print("\n2. Testing Generate Learning Path...")
                response = requests.post(
                    f"{BASE_URL}/api/ai/skills/learning-path",
                    headers=headers,
                    json={
                        "current_skills": "Python, JavaScript, React",
                        "target_role": "Full Stack Developer",
                        "hours_per_week": 10
                    }
                )
                data = response.json()
                
                if response.status_code == 200 and data.get("success"):
                    print_success("Learning path generated")
                    print_info(f"Duration: {data['data'].get('total_duration_weeks', 'N/A')} weeks")
                    return True
                else:
                    print_error(f"Learning path failed: {data}")
                    return False
            else:
                print_error(f"Skill gap analysis failed: {data}")
                return False
        except Exception as e:
            print_error(f"Skill gap test error: {e}")
            return False
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n" + "="*60)
        print("Testing Error Handling")
        print("="*60)
        
        if not self.token:
            print_warning("Skipping error handling tests (not authenticated)")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test validation error
        print("\n1. Testing Validation Error...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/ai/interview/start",
                headers=headers,
                json={
                    "role": "Software Developer"
                    # Missing required 'level' field
                }
            )
            data = response.json()
            
            if response.status_code == 400 and not data.get("success"):
                print_success("Validation error handled correctly")
                print_info(f"Error code: {data['error']['code']}")
                print_info(f"Error message: {data['error']['message']}")
                return True
            else:
                print_error("Validation error not handled correctly")
                return False
        except Exception as e:
            print_error(f"Error handling test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🧪 PHASE 2 ENDPOINT TESTING")
        print("="*60)
        
        results = []
        
        # Test health
        results.append(("Health Check", self.test_health()))
        
        # Test auth
        results.append(("Authentication", self.test_auth()))
        
        # Test resume endpoints
        results.append(("Resume Endpoints", self.test_resume_endpoints()))
        
        # Test interview endpoints
        results.append(("Interview Endpoints", self.test_interview_endpoints()))
        
        # Test skill gap endpoints
        results.append(("Skill Gap Endpoints", self.test_skill_gap_endpoints()))
        
        # Test error handling
        results.append(("Error Handling", self.test_error_handling()))
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
            print(f"{status} - {name}")
        
        print("="*60)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print(f"{GREEN}🎉 All tests passed! Phase 2 endpoints are working.{RESET}")
            return 0
        else:
            print(f"{YELLOW}⚠️  Some tests failed. Please review the errors above.{RESET}")
            return 1


def main():
    """Main function"""
    print(f"{BLUE}Starting Phase 2 endpoint tests...{RESET}")
    print(f"{BLUE}Make sure the backend server is running on {BASE_URL}{RESET}")
    
    tester = EndpointTester()
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
