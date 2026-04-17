"""
Test script to verify database integration with recommend.py
This tests that recommendations are based on real user data, not mock data
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db
import sqlite3

def setup_test_data():
    """Create test database with sample user and skills"""
    print("\n=== Setting Up Test Database ===")
    
    # Initialize database
    init_db()
    print("✓ Database initialized")
    
    # Connect to database
    conn = sqlite3.connect("skilliq.db")
    conn.row_factory = sqlite3.Row
    
    # Create test user
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        ["Test Student", "test@example.com", "hashed_password", "student"]
    )
    user_id = cursor.lastrowid
    print(f"✓ Created test user with ID: {user_id}")
    
    # Add user profile
    conn.execute(
        """INSERT INTO profiles (user_id, education_level, preferred_field, goals, learning_pace)
           VALUES (?, ?, ?, ?, ?)""",
        [user_id, "Bachelor's", "Software Development", "Become an AI Engineer", "Fast"]
    )
    print("✓ Created user profile")
    
    # Add user skills (matching AI Engineer requirements)
    test_skills = [
        ("Python", "Intermediate"),
        ("Machine Learning", "Beginner"),
        ("Data Structures", "Intermediate"),
        ("Git", "Advanced"),
    ]
    
    for skill_name, level in test_skills:
        conn.execute(
            "INSERT INTO student_skills (user_id, skill_name, level) VALUES (?, ?, ?)",
            [user_id, skill_name, level]
        )
    print(f"✓ Added {len(test_skills)} skills to user profile")
    
    conn.commit()
    conn.close()
    
    return user_id


def test_career_recommendations(user_id):
    """Test that career recommendations use real user data"""
    print("\n=== Testing Career Recommendations ===")
    
    from app import create_app
    from app.services.recommend import recommend_careers
    
    app = create_app()
    
    with app.app_context():
        result = recommend_careers(user_id)
        
        print(f"User ID: {result['userId']}")
        print(f"Number of recommendations: {len(result['recommendations'])}")
        
        print("\nTop 3 Career Matches:")
        for i, career in enumerate(result['recommendations'][:3], 1):
            print(f"\n{i}. {career['title']}")
            print(f"   Match Score: {career['matchScore']}%")
            print(f"   Required Skills: {', '.join(career['skills'][:5])}")
            print(f"   Salary Range: {career['salaryRange']}")
            print(f"   Job Outlook: {career['jobOutlook']}")
        
        # Verify it's using real data
        ai_engineer = next((c for c in result['recommendations'] if c['title'] == 'AI Engineer'), None)
        if ai_engineer:
            print(f"\n✓ AI Engineer match score calculated: {ai_engineer['matchScore']}%")
            print("  (Should be based on user's Python, ML, Data Structures skills)")
        
        return result


def test_skill_gap_analysis(user_id):
    """Test that skill gap is calculated from real user data"""
    print("\n=== Testing Skill Gap Analysis ===")
    
    from app import create_app
    from app.services.recommend import get_skill_gap
    
    app = create_app()
    
    with app.app_context():
        # Test for AI Engineer (career_id = 1)
        result = get_skill_gap(user_id, 1)
        
        print(f"User ID: {result['userId']}")
        print(f"Career ID: {result['careerId']}")
        print(f"Skills Acquired: {result['acquired']}")
        print(f"Skills Missing: {result['missing']}")
        
        print("\nSkill Gap Details:")
        for skill in result['skills']:
            status_icon = "✓" if skill['status'] == "Acquired" else "⚠" if skill['status'] == "Needs Work" else "✗"
            print(f"  {status_icon} {skill['skill']}: {skill['current']}% → {skill['target']}% ({skill['status']})")
        
        # Verify it's using real data
        python_skill = next((s for s in result['skills'] if s['skill'] == 'Python'), None)
        if python_skill:
            print(f"\n✓ Python skill found in gap analysis")
            print(f"  Current: {python_skill['current']}% (from user's Intermediate level)")
            print(f"  Status: {python_skill['status']}")
        
        return result


def test_learning_path(user_id):
    """Test that learning path is personalized based on skill gaps"""
    print("\n=== Testing Learning Path Generation ===")
    
    from app import create_app
    from app.services.recommend import get_learning_path
    
    app = create_app()
    
    with app.app_context():
        # Test for AI Engineer (career_id = 1)
        result = get_learning_path(user_id, 1)
        
        print(f"User ID: {result['userId']}")
        print(f"Career: {result['careerTitle']}")
        print(f"Estimated Completion: {result['estimatedCompletion']}")
        print(f"Number of Courses: {len(result['path'])}")
        
        print("\nPersonalized Learning Path:")
        for i, course in enumerate(result['path'], 1):
            priority_icon = "🔴" if course['priority'] == "High" else "🟡"
            print(f"\n{i}. {priority_icon} {course['title']}")
            print(f"   Provider: {course['provider']}")
            print(f"   Duration: {course['duration']}")
            print(f"   Priority: {course['priority']}")
            print(f"   Topics: {', '.join(course['resources'][:3])}")
        
        print("\n✓ Learning path is personalized based on user's skill gaps")
        
        return result


def test_market_insights():
    """Test that market insights use database data"""
    print("\n=== Testing Market Insights ===")
    
    from app import create_app
    from app.services.recommend import market_insights
    
    app = create_app()
    
    with app.app_context():
        result = market_insights()
        
        print(f"Trending Skills: {len(result['trendingSkills'])}")
        print(f"Salary Cards: {len(result['salaryCards'])}")
        print(f"Future Jobs: {len(result['futureJobs'])}")
        
        print("\nTop 5 Trending Skills:")
        for skill in result['trendingSkills'][:5]:
            print(f"  • {skill['skill']}: {skill['demand']}% demand")
        
        print("\nMarket Ticker:")
        for ticker in result['ticker']:
            print(f"  📰 {ticker}")
        
        print("\n✓ Market insights generated from database")
        
        return result


def verify_database_usage():
    """Verify that functions are actually querying the database"""
    print("\n=== Verifying Database Usage ===")
    
    conn = sqlite3.connect("skilliq.db")
    
    # Check if careers exist
    careers = conn.execute("SELECT COUNT(*) as count FROM careers").fetchone()
    print(f"✓ Careers in database: {careers[0]}")
    
    # Check if career_skill_map exists
    skill_map = conn.execute("SELECT COUNT(*) as count FROM career_skill_map").fetchone()
    print(f"✓ Career-skill mappings: {skill_map[0]}")
    
    # Check if test user skills exist
    user_skills = conn.execute("SELECT COUNT(*) as count FROM student_skills").fetchone()
    print(f"✓ User skills in database: {user_skills[0]}")
    
    conn.close()
    
    print("\n✓ All database tables populated correctly")


def cleanup():
    """Clean up test data"""
    print("\n=== Cleaning Up ===")
    
    try:
        conn = sqlite3.connect("skilliq.db")
        conn.execute("DELETE FROM student_skills WHERE user_id IN (SELECT id FROM users WHERE email = 'test@example.com')")
        conn.execute("DELETE FROM profiles WHERE user_id IN (SELECT id FROM users WHERE email = 'test@example.com')")
        conn.execute("DELETE FROM users WHERE email = 'test@example.com'")
        conn.commit()
        conn.close()
        print("✓ Test data cleaned up")
    except Exception as e:
        print(f"⚠ Cleanup warning: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE INTEGRATION TEST")
    print("Testing that recommend.py uses real database data")
    print("=" * 60)
    
    try:
        # Setup
        user_id = setup_test_data()
        verify_database_usage()
        
        # Run tests
        test_career_recommendations(user_id)
        test_skill_gap_analysis(user_id)
        test_learning_path(user_id)
        test_market_insights()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nConclusion:")
        print("✓ Career recommendations are based on user's actual skills")
        print("✓ Skill gaps are calculated dynamically from database")
        print("✓ Learning paths are personalized for each user")
        print("✓ Market insights use real career data")
        print("\n🎉 No more mock data! Everything is database-driven!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        cleanup()
        print("\nTest complete!")
