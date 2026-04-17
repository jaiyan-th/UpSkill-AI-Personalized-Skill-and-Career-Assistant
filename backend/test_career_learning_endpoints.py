"""
Test script for career and learning path endpoints
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_endpoints():
    print("=" * 60)
    print("Testing Career & Learning Path Endpoints")
    print("=" * 60)
    
    # Step 1: Register a test user
    print("\n1. Registering test user...")
    register_data = {
        "name": "Test User",
        "email": f"test_career_{hash('test')}@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("✓ User registered successfully")
            token = response.json().get("token")
        else:
            # Try to login if user exists
            login_response = requests.post(f"{BASE_URL}/auth/login", json={
                "email": register_data["email"],
                "password": register_data["password"]
            })
            token = login_response.json().get("token")
            print("✓ User logged in")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Add some skills
    print("\n2. Adding skills to user profile...")
    skills = [
        {"skill_name": "Python", "level": "Intermediate"},
        {"skill_name": "Machine Learning", "level": "Beginner"},
        {"skill_name": "SQL", "level": "Advanced"}
    ]
    
    try:
        for skill in skills:
            response = requests.post(f"{BASE_URL}/profile/skills", json=skill, headers=headers)
        print(f"✓ Added {len(skills)} skills")
    except Exception as e:
        print(f"✗ Error adding skills: {e}")
    
    # Step 3: Test Careers endpoint
    print("\n3. Testing /api/careers endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/careers", headers=headers)
        if response.status_code == 200:
            data = response.json()
            careers = data.get("careers", [])
            print(f"✓ Careers endpoint working!")
            print(f"  Found {len(careers)} career recommendations")
            if careers:
                print(f"\n  Top Career Match:")
                top = careers[0]
                print(f"    - Title: {top['title']}")
                print(f"    - Match Score: {top['match_score']}%")
                print(f"    - Salary: {top['salary_range']}")
                print(f"    - Required Skills: {', '.join(top['skills'][:3])}")
        else:
            print(f"✗ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Step 4: Test Learning Path endpoint
    print("\n4. Testing /api/learning-path endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/learning-path", headers=headers)
        if response.status_code == 200:
            data = response.json()
            courses = data.get("courses", [])
            print(f"✓ Learning Path endpoint working!")
            print(f"  Found {len(courses)} recommended courses")
            print(f"  Career: {data.get('careerTitle', 'N/A')}")
            print(f"  Estimated Completion: {data.get('estimatedCompletion', 'N/A')}")
            
            if courses:
                print(f"\n  First 3 Courses:")
                for i, course in enumerate(courses[:3], 1):
                    print(f"    {i}. {course['title']}")
                    print(f"       Provider: {course['provider']} | Duration: {course['duration']}")
                    print(f"       Priority: {course['priority']}")
        else:
            print(f"✗ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_endpoints()
