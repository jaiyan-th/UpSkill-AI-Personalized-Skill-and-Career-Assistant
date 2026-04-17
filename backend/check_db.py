import sqlite3

conn = sqlite3.connect('skilliq.db')
cursor = conn.cursor()

# Check tables
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])

# Check if proctor_logs exists
if ('proctor_logs',) in tables:
    print("✓ proctor_logs table exists")
else:
    print("✗ proctor_logs table missing")

# Check interview_sessions columns
columns = cursor.execute("PRAGMA table_info(interview_sessions)").fetchall()
print("\ninterview_sessions columns:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Check users
users = cursor.execute("SELECT id, name, email FROM users").fetchall()
print(f"\nUsers in database: {len(users)}")
for user in users:
    print(f"  - ID: {user[0]}, Name: {user[1]}, Email: {user[2]}")

conn.close()
