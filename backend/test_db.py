import sys
from dotenv import load_dotenv
load_dotenv('c:/Users/jaiya/Documents/UpSkill AI-Skill Assistant/UpSkill AI-Skill Assistant/backend/.env')
sys.path.append('c:/Users/jaiya/Documents/UpSkill AI-Skill Assistant/UpSkill AI-Skill Assistant/backend')
from app.database import get_db
from app import create_app
app = create_app()
with app.app_context():
    db = get_db()
    resumes = db.execute('SELECT id, analysis_data FROM resumes ORDER BY uploaded_at DESC LIMIT 1').fetchall()
    for r in resumes:
        print("ID:", r['id'])
        print("Data:", r['analysis_data'])
