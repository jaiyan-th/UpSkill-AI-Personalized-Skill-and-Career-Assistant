"""
Resume History Routes
API endpoints for resume analysis history
"""

from flask import Blueprint, jsonify
from app.auth_utils import require_auth
from app.database import get_db
import json

resume_history_bp = Blueprint('resume_history', __name__, url_prefix='/api/resume')

@resume_history_bp.route('/history', methods=['GET'])
@require_auth
def get_resume_history(current_user):
    """
    Get user's resume analysis history
    
    Response:
        {
            "success": true,
            "history": [
                {
                    "id": 1,
                    "file_name": "resume.pdf",
                    "ats_score": 80,
                    "uploaded_at": "2026-04-09T10:30:00",
                    "analysis_summary": {...}
                }
            ],
            "stats": {
                "total_resumes": 3,
                "average_ats_score": 75,
                "latest_score": 80
            }
        }
    """
    try:
        user_id = current_user['id']
        db = get_db()
        
        # Get all resumes for user
        resumes = db.execute(
            """SELECT id, file_name, ats_score, uploaded_at, analysis_data, target_role
               FROM resumes 
               WHERE user_id = ? 
               ORDER BY uploaded_at DESC""",
            [user_id]
        ).fetchall()
        
        history = []
        total_score = 0
        
        for resume in resumes:
            analysis_data = {}
            if resume['analysis_data']:
                try:
                    analysis_data = json.loads(resume['analysis_data'])
                except Exception:
                    pass
            
            # analysis_data is the raw result from ats_analyzer:
            # { score, matched_keywords, missing_keywords, suggestions, extracted_data }
            extracted = analysis_data.get('extracted_data', {})
            skills = extracted.get('skills', [])
            matched_kw = analysis_data.get('matched_keywords', [])
            missing_kw = analysis_data.get('missing_keywords', [])

            suggestions = analysis_data.get('suggestions', [])
            breakdown = analysis_data.get('breakdown', {})

            history.append({
                'id': resume['id'],
                'file_name': resume['file_name'],
                'ats_score': resume['ats_score'],
                'uploaded_at': resume['uploaded_at'],
                'target_role': resume['target_role'] or '—',
                'skills_count': len(skills),
                'matched_keywords': len(matched_kw),
                'missing_keywords': len(missing_kw),
                'skills': [s['name'] if isinstance(s, dict) else s for s in skills],
                'matched_kw_list': matched_kw,
                'missing_kw_list': missing_kw,
                'suggestions': suggestions,
                'breakdown': breakdown,
            })
            
            total_score += resume['ats_score'] or 0
        
        stats = {
            'total_resumes': len(resumes),
            'average_ats_score': round(total_score / len(resumes)) if resumes else 0,
            'latest_score': resumes[0]['ats_score'] if resumes else 0
        }
        
        return jsonify({
            'success': True,
            'history': history,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Error in get_resume_history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500
