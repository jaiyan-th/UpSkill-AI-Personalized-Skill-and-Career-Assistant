import sqlite3
db = sqlite3.connect('skilliq.db')
sql = "UPDATE interview_sessions SET status='completed', overall_score=0, ended_at=datetime('now') WHERE status='in_progress'"
db.execute(sql)
db.commit()
print('Fixed:', db.total_changes)
db.close()
