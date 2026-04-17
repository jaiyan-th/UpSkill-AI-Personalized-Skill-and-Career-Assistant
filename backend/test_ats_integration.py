"""
Test script for enhanced ATS analysis with profile integration
Run this after starting the Flask server to test the new features
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_ats_analysis_basic():
    """Test basic ATS analysis without profile update"""
    print("\n=== Test 1: Basic ATS Analysis ===")
    
    # Create a sample resume text file
    sample_resume = """
    John Doe
    Software Engineer
    john.doe@email.com | +1-234-567-8900
    
    EDUCATION
    Bachelor of Technology in Computer Science
    XYZ University, 2020
    
    EXPERIENCE
    Software Developer at Tech Corp (2020-2023)
    - Developed web applications using React and Node.js
    - Implemented RESTful APIs with Python and Flask
    - Worked with SQL databases and MongoDB
    - Built machine learning models using TensorFlow
    - Led a team of 3 developers on microservices architecture
    
    SKILLS
    Python (Advanced), JavaScript (Intermediate), React (Intermediate)
    SQL, MongoDB, TensorFlow, Docker, Git, AWS
    Leadership, Communication, Problem Solving
    """
    
    job_description = """
    We are looking for a Senior AI Engineer with:
    - 3+ years of Python experience
    - Strong machine learning background
    - Experience with TensorFlow or PyTorch
    - Knowledge of Docker and Kubernetes
    - Cloud experience (AWS/GCP)
    """
    
    # Save sample resume to file
    with open('sample_resume.txt', 'w') as f:
        f.write(sample_resume)
    
    # Upload and analyze
    with open('sample_resume.txt', 'rb') as f:
        files = {'file': ('sample_resume.txt', f, 'text/plain')}
        data = {'job_description': job_description}
        
        response = requests.post(f"{BASE_URL}/ats/analyze", files=files, data=data)
        result = response.json()
    
    print(f"ATS Score: {result['score']}/100")
    print(f"Matched Keywords: {', '.join(result['matched_keywords'][:10])}")
    print(f"Missing Keywords: {', '.join(result['missing_keywords'][:5])}")
    print(f"\nExtracted Skills ({len(result['extracted_data']['skills'])}):")
    for skill in result['extracted_data']['skills'][:10]:
        print(f"  - {skill['name']}: {skill['level']} ({skill['category']})")
    print(f"\nEducation: {result['extracted_data']['education_level']}")
    print(f"Experience: {result['extracted_data']['experience_years']} years")
    
    return result


def test_ats_with_profile_update():
    """Test ATS analysis with automatic profile update"""
    print("\n=== Test 2: ATS Analysis with Profile Update ===")
    
    # First, register a test user
    user_data = {
        "name": "Test User",
        "email": f"test_{hash('test')}@example.com",
        "password": "testpass123",
        "role": "student"
    }
    
    try:
        register_response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if register_response.status_code == 201:
            user_id = register_response.json()['user']['id']
            print(f"Created test user with ID: {user_id}")
        else:
            print("User might already exist, using ID 1 for testing")
            user_id = 1
    except Exception as e:
        print(f"Using default user ID 1: {e}")
        user_id = 1
    
    # Upload resume with auto-update enabled
    with open('sample_resume.txt', 'rb') as f:
        files = {'file': ('sample_resume.txt', f, 'text/plain')}
        data = {
            'job_description': 'AI Engineer position requiring Python, ML, TensorFlow',
            'user_id': str(user_id),
            'auto_update_profile': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/ats/analyze", files=files, data=data)
        result = response.json()
    
    print(f"Profile Updated: {result.get('profile_updated', False)}")
    if result.get('profile_updated'):
        print("✓ Skills automatically saved to user profile")
    
    if 'recommendations' in result:
        print("\n=== Career Recommendations ===")
        for career in result['recommendations']['top_careers']:
            print(f"\n{career['career']} - Match Score: {career['match_score']}%")
            print(f"  Matched Skills: {', '.join(career['matched_skills'][:5])}")
            if career['missing_skills']:
                print(f"  Missing Skills: {', '.join(career['missing_skills'])}")
        
        print("\n=== Learning Recommendations ===")
        for rec in result['recommendations']['learning_recommendations'][:3]:
            print(f"  • {rec['skill']} ({rec['priority']} priority) - {rec['estimated_time']}")
        
        readiness = result['recommendations']['overall_readiness']
        print(f"\n=== Job Readiness ===")
        print(f"Score: {readiness['score']}/100 - {readiness['status']}")
        print(f"Message: {readiness['message']}")
    
    return result


def test_skill_extraction_accuracy():
    """Test skill extraction with various resume formats"""
    print("\n=== Test 3: Skill Extraction Accuracy ===")
    
    test_cases = [
        {
            "name": "Senior Developer",
            "text": "Expert in Python with 7+ years experience. Advanced React developer. Proficient in AWS architecture.",
            "expected_levels": {"python": "Advanced", "react": "Advanced", "aws": "Advanced"}
        },
        {
            "name": "Junior Developer",
            "text": "Familiar with JavaScript and HTML. Basic knowledge of CSS and Git.",
            "expected_levels": {"javascript": "Beginner", "html": "Beginner"}
        },
        {
            "name": "Mid-level Developer",
            "text": "3 years experience with Node.js. Developed multiple applications using MongoDB. Worked with Docker.",
            "expected_levels": {"node": "Intermediate", "mongodb": "Intermediate", "docker": "Intermediate"}
        }
    ]
    
    for case in test_cases:
        with open('test_resume.txt', 'w') as f:
            f.write(case['text'])
        
        with open('test_resume.txt', 'rb') as f:
            files = {'file': ('test_resume.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/ats/analyze", files=files)
            result = response.json()
        
        print(f"\n{case['name']}:")
        extracted = {s['name'].lower(): s['level'] for s in result['extracted_data']['skills']}
        
        for skill, expected_level in case['expected_levels'].items():
            actual_level = extracted.get(skill, "Not Found")
            match = "✓" if actual_level == expected_level else "✗"
            print(f"  {match} {skill.title()}: Expected {expected_level}, Got {actual_level}")


if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced ATS Analysis Integration Tests")
    print("=" * 60)
    print("\nMake sure the Flask server is running on http://localhost:5000")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()
    
    try:
        # Run tests
        test_ats_analysis_basic()
        test_ats_with_profile_update()
        test_skill_extraction_accuracy()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Flask server.")
        print("Please start the server with: python run.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
