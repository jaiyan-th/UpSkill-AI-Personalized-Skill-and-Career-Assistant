import sqlite3
from app.auth_utils import hash_password

conn = sqlite3.connect('skilliq.db')
cursor = conn.cursor()

# Check if user 8 exists
existing = cursor.execute("SELECT id FROM users WHERE id = 8").fetchone()

if existing:
    print("User ID 8 already exists")
else:
    # Create user with ID 8
    password_hash = hash_password("password123")  # Default password
    
    cursor.execute("""
        INSERT INTO users (id, name, email, password_hash, role, created_at)
        VALUES (8, 'Kanith', 'kanith@gmail.com', ?, 'student', datetime('now'))
    """, [password_hash])
    
    conn.commit()
    print("✓ Created user: Kanith (ID: 8, Email: kanith@gmail.com)")
    print("  Password: password123")

conn.close()
