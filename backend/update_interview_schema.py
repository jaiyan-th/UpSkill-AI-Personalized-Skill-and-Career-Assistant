#!/usr/bin/env python3
"""
Update database schema for enhanced interview system
Adds: duration_minutes, type, content_score, communication_score to interview tables
Adds: proctor_logs table
"""

import sqlite3
import os

def update_schema():
    db_path = os.getenv("DATABASE_PATH", "skilliq.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Updating interview database schema...")
    
    try:
        # Add duration_minutes to interview_sessions if not exists
        cursor.execute("PRAGMA table_info(interview_sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'duration_minutes' not in columns:
            cursor.execute("ALTER TABLE interview_sessions ADD COLUMN duration_minutes INTEGER DEFAULT 4")
            print("  ✅ Added duration_minutes to interview_sessions")
        
        # Add type, content_score, communication_score to interview_qa if not exists
        cursor.execute("PRAGMA table_info(interview_qa)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'type' not in columns:
            cursor.execute("ALTER TABLE interview_qa ADD COLUMN type TEXT DEFAULT 'general'")
            print("  ✅ Added type to interview_qa")
        
        if 'content_score' not in columns:
            cursor.execute("ALTER TABLE interview_qa ADD COLUMN content_score INTEGER DEFAULT 0")
            print("  ✅ Added content_score to interview_qa")
        
        if 'communication_score' not in columns:
            cursor.execute("ALTER TABLE interview_qa ADD COLUMN communication_score INTEGER DEFAULT 0")
            print("  ✅ Added communication_score to interview_qa")
        
        # Create proctor_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proctor_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
                event_type TEXT NOT NULL,
                details TEXT,
                image_path TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✅ Created proctor_logs table")
        
        conn.commit()
        print("\n🎉 Schema update completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error updating schema: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    update_schema()
