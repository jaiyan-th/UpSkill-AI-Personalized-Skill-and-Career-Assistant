"""
Quick Setup Script for UpSkill AI Backend
Initializes database and checks configuration
"""

import os
import sys
from dotenv import load_dotenv

# Load .env file first
load_dotenv()

from app.database import init_db
from app.config import Config

def check_env_vars():
    """Check if required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = {
        'GROQ_API_KEY': 'Groq API key for LLM services',
        'JWT_SECRET': 'Secret key for JWT tokens'
    }
    
    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"  ❌ {var}: {description}")
            print(f"  ❌ {var} - NOT SET")
        else:
            print(f"  ✅ {var} - SET")
    
    if missing:
        print("\n⚠️  Missing required environment variables:")
        for msg in missing:
            print(msg)
        print("\nPlease set them in your .env file or environment.")
        print("\nExample .env file:")
        print("=" * 50)
        print("GROQ_API_KEY=your_groq_api_key_here")
        print("JWT_SECRET=your_super_secret_key_here")
        print("DATABASE_PATH=skilliq.db")
        print("GROQ_MODEL=llama-3.1-70b-versatile")
        print("=" * 50)
        return False
    
    return True

def initialize_database():
    """Initialize the database"""
    print("\n📊 Initializing database...")
    try:
        init_db()
        print("  ✅ Database initialized successfully!")
        print(f"  📁 Database location: {Config.DATABASE_PATH}")
        return True
    except Exception as e:
        print(f"  ❌ Database initialization failed: {e}")
        return False

def test_llm_connection():
    """Test LLM service connection"""
    print("\n🤖 Testing LLM connection...")
    try:
        from app.services.llm_service import LLMService
        llm = LLMService()
        
        if llm.groq_key:
            print("  ✅ Groq API key found")
            # Quick test
            try:
                response = llm.generate(
                    prompt="Say 'Hello' in one word",
                    system_prompt="You are a helpful assistant.",
                    max_tokens=10
                )
                print(f"  ✅ LLM test successful! Response: {response[:50]}...")
                return True
            except Exception as e:
                print(f"  ⚠️  LLM test failed: {e}")
                print("  Note: This might be due to API rate limits or network issues")
                return True  # Don't fail setup for this
        else:
            print("  ⚠️  No LLM API key configured")
            return False
            
    except Exception as e:
        print(f"  ❌ LLM service error: {e}")
        return False

def print_next_steps():
    """Print next steps for user"""
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("\n1. Start the backend server:")
    print("   python run.py")
    print("\n2. Server will run at: http://localhost:5000")
    print("\n3. Test the API:")
    print("   curl http://localhost:5000/health")
    print("\n4. Start the frontend:")
    print("   cd ../frontend")
    print("   python server.py")
    print("\n5. Open browser: http://localhost:8000")
    print("\n📚 Documentation:")
    print("   - API Docs: API_DOCUMENTATION.md")
    print("   - Implementation Guide: ../IMPLEMENTATION_GUIDE.md")
    print("\n🚀 Ready to build amazing AI-powered career tools!")
    print("=" * 60)

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 UpSkill AI - Backend Setup")
    print("=" * 60)
    
    # Check environment variables
    if not check_env_vars():
        print("\n❌ Setup failed: Missing environment variables")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("\n❌ Setup failed: Database initialization error")
        sys.exit(1)
    
    # Test LLM connection
    test_llm_connection()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
