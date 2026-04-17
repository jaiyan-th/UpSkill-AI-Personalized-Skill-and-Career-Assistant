#!/usr/bin/env python3
"""Reset all user-related data from the database"""
import sqlite3

def reset_database():
    conn = sqlite3.connect('skilliq.db')
    cursor = conn.cursor()
    
    print("🧹 Resetting database...")
    
    # Tables to clear (in order to respect foreign keys)
    tables_to_clear = [
        'progress_logs',
        'student_skills', 
        'student_interests',
        'profiles',
        'users'
    ]
    
    deleted_counts = {}
    
    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table}")
            deleted_counts[table] = cursor.rowcount
            conn.commit()
            print(f"  ✅ Cleared {deleted_counts[table]} records from {table}")
        except sqlite3.Error as e:
            print(f"  ⚠️  Could not clear {table}: {e}")
    
    # Verify users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    print(f"\n📊 Final Status:")
    print(f"  - Users in database: {user_count}")
    
    conn.close()
    
    if user_count == 0:
        print("\n🎉 Database reset successfully! All user data cleared.")
    else:
        print("\n⚠️  Warning: Some users may still exist.")

if __name__ == '__main__':
    reset_database()
