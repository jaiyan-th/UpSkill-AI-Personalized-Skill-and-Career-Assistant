#!/usr/bin/env python3
"""Clear all user data from the database"""
import sqlite3

def clear_users():
    conn = sqlite3.connect('skilliq.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("📊 Database Tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Delete from users table
    cursor.execute("DELETE FROM users")
    deleted = cursor.rowcount
    conn.commit()
    
    print(f"\n✅ Deleted {deleted} user(s) from database")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"✅ Remaining users: {count}")
    
    conn.close()
    print("\n🎉 Database cleared successfully!")

if __name__ == '__main__':
    clear_users()
