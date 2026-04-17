"""
Migration script to add fluency and pronunciation fields to interview_qa table
"""

import sqlite3
import os

def migrate_database():
    db_path = os.getenv("DATABASE_PATH", "UpSkill.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting migration...")
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(interview_qa)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add new columns if they don't exist
        if 'content_score' not in columns:
            print("Adding content_score column...")
            cursor.execute("ALTER TABLE interview_qa ADD COLUMN content_score REAL DEFAULT 5.0")
        
        if 'communication_score' not in columns:
            print("Adding communication_score column...")
            cursor.execute("ALTER TABLE interview_qa ADD COLUMN communication_score REAL DEFAULT 5.0")
        
        if 'fluency_score' not in columns:
            print("Adding fluency_score column...")
            cursor.execute("ALTER TABLE interview_qa ADD COLUMN fluency_score REAL DEFAULT 5.0")
        
        if 'pronunciation_score' not in columns:
            print("Adding pronunciation_score column...")
            cursor.execute("ALTER TABLE interview_qa ADD COLUMN pronunciation_score REAL DEFAULT 5.0")
        
        if 'speech_analysis' not in columns:
            print("Adding speech_analysis column...")
            cursor.execute("ALTER TABLE interview_qa ADD COLUMN speech_analysis TEXT")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
