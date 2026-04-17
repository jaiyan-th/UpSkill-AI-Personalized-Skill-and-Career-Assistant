"""
Fix profiles table - Add target_role column if missing
"""

import sqlite3
import os

def fix_profiles_table():
    db_path = os.getenv("DATABASE_PATH", "skilliq.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if target_role column exists
    cursor.execute("PRAGMA table_info(profiles)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'target_role' not in columns:
        print("Adding target_role column to profiles table...")
        cursor.execute("ALTER TABLE profiles ADD COLUMN target_role TEXT")
        conn.commit()
        print("✓ target_role column added successfully")
    else:
        print("✓ target_role column already exists")
    
    # Verify users table exists and has data
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"✓ Users table has {user_count} users")
    
    # Check for orphaned records in profiles
    cursor.execute("""
        SELECT COUNT(*) FROM profiles 
        WHERE user_id NOT IN (SELECT id FROM users)
    """)
    orphaned = cursor.fetchone()[0]
    
    if orphaned > 0:
        print(f"⚠ Found {orphaned} orphaned profile records")
        print("Cleaning up orphaned records...")
        cursor.execute("""
            DELETE FROM profiles 
            WHERE user_id NOT IN (SELECT id FROM users)
        """)
        conn.commit()
        print("✓ Orphaned records cleaned up")
    else:
        print("✓ No orphaned profile records found")
    
    # Check for orphaned records in chat_messages
    cursor.execute("""
        SELECT COUNT(*) FROM chat_messages 
        WHERE user_id NOT IN (SELECT id FROM users)
    """)
    orphaned_chat = cursor.fetchone()[0]
    
    if orphaned_chat > 0:
        print(f"⚠ Found {orphaned_chat} orphaned chat message records")
        print("Cleaning up orphaned chat messages...")
        cursor.execute("""
            DELETE FROM chat_messages 
            WHERE user_id NOT IN (SELECT id FROM users)
        """)
        conn.commit()
        print("✓ Orphaned chat messages cleaned up")
    else:
        print("✓ No orphaned chat message records found")
    
    conn.close()
    print("\n✓ Database fix completed successfully!")

if __name__ == "__main__":
    fix_profiles_table()
