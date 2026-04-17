#!/usr/bin/env python3
"""Clear ALL user data from the database - complete reset"""
import sqlite3
import os

def clear_all_data():
    db_path = 'skilliq.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🧹 Clearing ALL user data from database...\n")
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [t[0] for t in cursor.fetchall()]
    
    print("📊 Found tables:")
    for table in all_tables:
        print(f"  - {table}")
    
    print("\n🗑️  Deleting data...\n")
    
    # Tables to clear (in order to respect foreign keys)
    # Clear child tables first, then parent tables
    tables_to_clear = [
        'chat_messages',
        'interview_qa',
        'interview_sessions',
        'learning_path_resources',
        'learning_paths',
        'skill_gap_analysis',
        'user_skill_graph',
        'resumes',
        'progress_logs',
        'student_skills',
        'student_interests',
        'profiles',
        'users'
    ]
    
    deleted_counts = {}
    
    for table in tables_to_clear:
        if table in all_tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                deleted_counts[table] = cursor.rowcount
                conn.commit()
                print(f"  ✅ Cleared {deleted_counts[table]:>4} records from {table}")
            except sqlite3.Error as e:
                print(f"  ⚠️  Could not clear {table}: {e}")
        else:
            print(f"  ⏭️  Skipped {table} (table doesn't exist)")
    
    # Verify all user data is cleared
    print("\n📊 Verification:")
    for table in ['users', 'profiles', 'interview_sessions', 'resumes']:
        if table in all_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            status = "✅" if count == 0 else "⚠️"
            print(f"  {status} {table}: {count} records")
    
    conn.close()
    
    print("\n🎉 Database cleared successfully! All user data has been deleted.")
    print("💡 You can now create fresh user accounts.")

if __name__ == '__main__':
    confirm = input("⚠️  This will DELETE ALL user data. Are you sure? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_all_data()
    else:
        print("❌ Operation cancelled.")
