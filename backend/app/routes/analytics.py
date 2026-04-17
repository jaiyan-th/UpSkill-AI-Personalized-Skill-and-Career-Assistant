"""
Analytics API Routes
Provides dashboard, trends, insights, and performance analytics
"""

from flask import Blueprint, request, jsonify
from app.auth_utils import require_auth
from app.services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
analytics_service = AnalyticsService()

@analytics_bp.route('/dashboard', methods=['GET'])
@require_auth
def get_dashboard(current_user):
    """
    Get comprehensive dashboard for user
    
    Response:
        {
            "success": true,
            "dashboard": {
                "overview": {...},
                "interview_history": [...],
                "skill_analyses": [...],
                "learning_paths": [...]
            }
        }
    """
    try:
        user_id = current_user['id']
        dashboard = analytics_service.get_user_dashboard(user_id)
        
        return jsonify({
            "success": True,
            "dashboard": dashboard
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@analytics_bp.route('/trends', methods=['GET'])
@require_auth
def get_trends(current_user):
    """
    Get interview performance trends
    
    Query params:
        days: Number of days to analyze (default: 30)
    
    Response:
        {
            "success": true,
            "trends": {
                "score_trend": [...],
                "improvement_rate": 5.2,
                "best_performance": {...}
            }
        }
    """
    try:
        user_id = current_user['id']
        days = int(request.args.get('days', 30))
        
        trends = analytics_service.get_interview_trends(user_id, days)
        
        return jsonify({
            "success": True,
            "trends": trends
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@analytics_bp.route('/skill-progress', methods=['GET'])
@require_auth
def get_skill_progress(current_user):
    """
    Get skill development progress over time
    
    Response:
        {
            "success": true,
            "progress": {
                "skills_acquired": [...],
                "skill_timeline": [...]
            }
        }
    """
    try:
        user_id = current_user['id']
        progress = analytics_service.get_skill_progress(user_id)
        
        return jsonify({
            "success": True,
            "progress": progress
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@analytics_bp.route('/learning', methods=['GET'])
@require_auth
def get_learning_analytics(current_user):
    """
    Get learning path analytics
    
    Response:
        {
            "success": true,
            "learning": {
                "active_paths": [...],
                "total_hours_invested": 120,
                "completion_rate": 0.65
            }
        }
    """
    try:
        user_id = current_user['id']
        learning = analytics_service.get_learning_analytics(user_id)
        
        return jsonify({
            "success": True,
            "learning": learning
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@analytics_bp.route('/achievements', methods=['GET'])
@require_auth
def get_achievements(current_user):
    """
    Get user achievements and milestones
    
    Response:
        {
            "success": true,
            "achievements": [
                {
                    "title": "First Interview",
                    "description": "...",
                    "earned_at": "...",
                    "icon": "🎤"
                }
            ]
        }
    """
    try:
        user_id = current_user['id']
        achievements = analytics_service.get_achievements(user_id)
        
        return jsonify({
            "success": True,
            "achievements": achievements,
            "total": len(achievements)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@analytics_bp.route('/insights', methods=['GET'])
@require_auth
def get_insights(current_user):
    """
    Get AI-powered insights and recommendations
    
    Response:
        {
            "success": true,
            "insights": {
                "key_insights": [...],
                "recommendations": [...],
                "focus_areas": [...],
                "overall_readiness": {...}
            }
        }
    """
    try:
        user_id = current_user['id']
        insights = analytics_service.generate_insights(user_id)
        
        return jsonify({
            "success": True,
            "insights": insights
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@analytics_bp.route('/summary', methods=['GET'])
@require_auth
def get_summary(current_user):
    """
    Get complete analytics summary (all data in one call)
    
    Response:
        {
            "success": true,
            "summary": {
                "dashboard": {...},
                "trends": {...},
                "insights": {...},
                "achievements": [...]
            }
        }
    """
    try:
        user_id = current_user['id']
        
        summary = {
            "dashboard": analytics_service.get_user_dashboard(user_id),
            "trends": analytics_service.get_interview_trends(user_id, 30),
            "insights": analytics_service.generate_insights(user_id),
            "achievements": analytics_service.get_achievements(user_id)
        }
        
        return jsonify({
            "success": True,
            "summary": summary
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
