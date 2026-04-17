import sqlite3

conn = sqlite3.connect('skilliq.db')
cursor = conn.cursor()

# Get user info
cursor.execute('SELECT id, name, email FROM users WHERE id=13')
user = cursor.fetchone()
print(f'User: {user[1]} ({user[2]})')

# Check resume
cursor.execute('SELECT COUNT(*) FROM resumes WHERE user_id=13')
resume_count = cursor.fetchone()[0]
print(f'Resumes: {resume_count}')

# Check completed interviews
cursor.execute('SELECT COUNT(*) FROM interview_sessions WHERE user_id=13 AND status="completed"')
interview_count = cursor.fetchone()[0]
print(f'Completed Interviews: {interview_count}')

# Check skill gap analysis
cursor.execute('SELECT COUNT(*) FROM skill_gap_analysis WHERE user_id=13')
gap_count = cursor.fetchone()[0]
print(f'Skill Gap Analyses: {gap_count}')

print(f'\n=== Status ===')
print(f'Has Resume: {"✅ Yes" if resume_count > 0 else "❌ No"}')
print(f'Has Interview: {"✅ Yes" if interview_count > 0 else "❌ No"}')
print(f'Has Gap Analysis: {"✅ Yes" if gap_count > 0 else "❌ No"}')

print(f'\n=== Next Step ===')
if resume_count == 0:
    print('📄 Upload Resume on Resume Analysis page')
elif gap_count == 0:
    print('🎯 Run Skill Gap Analysis on Skill Gap Analysis page')
else:
    print('📚 Learning Path should be available!')

conn.close()
