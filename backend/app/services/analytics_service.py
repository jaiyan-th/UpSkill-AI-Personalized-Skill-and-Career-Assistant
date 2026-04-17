"""
Analytics Service
Provides insights, trends, and performance analytics across the platform
"""

from datetime import datetime, timedelta
from typing import Dict, List
from app.database import get_db
import json

class AnalyticsService:
    def __init__(self):
        pass
    
    def get_user_dashboard(self, user_id: int) -> Dict:
        """
        Get comprehensive dashboard data for user
        
        Returns:
            {
                "overview": {...},
                "interview_history": [...],
                "skill_progress": {...},
                "learning_progress": {...},
                "achievements": [...]
            }
        """
        
        db = get_db()
        
        # Overview stats
        total_interviews = db.execute(
            "SELECT COUNT(*) as count FROM interview_sessions WHERE user_id = ?",
            [user_id]
        ).fetchone()['count']
        
        completed_interviews = db.execute(
            "SELECT COUNT(*) as count FROM interview_sessions WHERE user_id = ? AND status = 'completed'",
            [user_id]
        ).fetchone()['count']
        
        avg_score = db.execute(
            "SELECT AVG(overall_score) as avg FROM interview_sessions WHERE user_id = ? AND status = 'completed'",
            [user_id]
        ).fetchone()['avg'] or 0
        
        total_resumes = db.execute(
            "SELECT COUNT(*) as count FROM resumes WHERE user_id = ?",
            [user_id]
        ).fetchone()['count']
        
        # Recent interviews
        recent_interviews = db.execute(
            """SELECT session_id, role, level, overall_score, started_at, status
               FROM interview_sessions
               WHERE user_id = ?
               ORDER BY started_at DESC
               LIMIT 5""",
            [user_id]
        ).fetchall()
        
        # Skill gap analyses
        skill_analyses = db.execute(
            """SELECT analysis_id, target_role, readiness_score, created_at
               FROM skill_gap_analysis
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT 3""",
            [user_id]
        ).fetchall()
        
        # Learning paths
        learning_paths = db.execute(
            """SELECT path_id, target_role, status, progress_percentage, created_at
               FROM learning_paths
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT 3""",
            [user_id]
        ).fetchall()
        
        return {
            "overview": {
                "total_interviews": total_interviews,
                "completed_interviews": completed_interviews,
                "average_score": round(avg_score, 1),
                "total_resumes": total_resumes,
                "skill_analyses": len(skill_analyses),
                "active_learning_paths": sum(1 for lp in learning_paths if lp['status'] == 'in_progress')
            },
            "interview_history": [
                {
                    "session_id": i['session_id'],
                    "role": i['role'],
                    "level": i['level'],
                    "score": i['overall_score'],
                    "date": i['started_at'],
                    "status": i['status']
                } for i in recent_interviews
            ],
            "skill_analyses": [
                {
                    "analysis_id": s['analysis_id'],
                    "role": s['target_role'],
                    "readiness": s['readiness_score'],
                    "date": s['created_at']
                } for s in skill_analyses
            ],
            "learning_paths": [
                {
                    "path_id": lp['path_id'],
                    "role": lp['target_role'],
                    "status": lp['status'],
                    "progress": lp['progress_percentage'],
                    "date": lp['created_at']
                } for lp in learning_paths
            ]
        }
    
    def get_interview_trends(self, user_id: int, days: int = 30) -> Dict:
        """
        Get interview performance trends over time
        
        Returns:
            {
                "score_trend": [...],
                "interview_count_by_role": {...},
                "improvement_rate": 5.2,
                "best_performance": {...},
                "areas_improving": [...],
                "areas_declining": [...]
            }
        """
        
        db = get_db()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get interviews in time period
        interviews = db.execute(
            """SELECT session_id, role, level, overall_score, started_at
               FROM interview_sessions
               WHERE user_id = ? AND status = 'completed' AND started_at >= ?
               ORDER BY started_at""",
            [user_id, cutoff_date]
        ).fetchall()
        
        if not interviews:
            return {
                "score_trend": [],
                "interview_count_by_role": {},
                "improvement_rate": 0,
                "message": "No completed interviews in this period"
            }
        
        # Score trend
        score_trend = [
            {
                "date": i['started_at'],
                "score": i['overall_score'],
                "role": i['role']
            } for i in interviews
        ]
        
        # Count by role
        role_counts = {}
        for i in interviews:
            role_counts[i['role']] = role_counts.get(i['role'], 0) + 1
        
        # Calculate improvement rate
        if len(interviews) >= 2:
            first_score = interviews[0]['overall_score'] or 0
            last_score = interviews[-1]['overall_score'] or 0
            improvement_rate = last_score - first_score
        else:
            improvement_rate = 0
        
        # Best performance
        best = max(interviews, key=lambda x: x['overall_score'] or 0)
        
        return {
            "score_trend": score_trend,
            "interview_count_by_role": role_counts,
            "total_interviews": len(interviews),
            "average_score": sum(i['overall_score'] or 0 for i in interviews) / len(interviews),
            "improvement_rate": round(improvement_rate, 1),
            "best_performance": {
                "session_id": best['session_id'],
                "role": best['role'],
                "score": best['overall_score'],
                "date": best['started_at']
            },
            "trend_direction": "improving" if improvement_rate > 0 else "declining" if improvement_rate < 0 else "stable"
        }
    
    def get_skill_progress(self, user_id: int) -> Dict:
        """
        Track skill development over time
        
        Returns:
            {
                "skills_acquired": [...],
                "skills_improving": [...],
                "skills_mastered": [...],
                "skill_timeline": [...]
            }
        """
        
        db = get_db()
        
        # Get all skill gap analyses
        analyses = db.execute(
            """SELECT analysis_id, target_role, analysis_data, created_at
               FROM skill_gap_analysis
               WHERE user_id = ?
               ORDER BY created_at""",
            [user_id]
        ).fetchall()
        
        if not analyses:
            return {
                "skills_acquired": [],
                "skills_improving": [],
                "skills_mastered": [],
                "message": "No skill analyses available"
            }
        
        # Track skill changes over time
        skill_timeline = []
        all_skills = set()
        
        for analysis in analyses:
            try:
                data = json.loads(analysis['analysis_data'])
                strong_skills = data.get('strong_skills', [])
                missing_skills = data.get('missing_skills', [])
                
                skill_timeline.append({
                    "date": analysis['created_at'],
                    "role": analysis['target_role'],
                    "strong_count": len(strong_skills),
                    "missing_count": len(missing_skills),
                    "strong_skills": strong_skills,
                    "missing_skills": missing_skills
                })
                
                all_skills.update(strong_skills)
            except:
                continue
        
        # Identify skills acquired (missing in first, present in later)
        skills_acquired = []
        if len(skill_timeline) >= 2:
            first_missing = set(s.get('skill', s) if isinstance(s, dict) else s 
                              for s in skill_timeline[0]['missing_skills'])
            last_strong = set(s.get('name', s) if isinstance(s, dict) else s 
                            for s in skill_timeline[-1]['strong_skills'])
            skills_acquired = list(first_missing.intersection(last_strong))
        
        return {
            "skills_acquired": skills_acquired,
            "total_skills_tracked": len(all_skills),
            "skill_timeline": skill_timeline,
            "latest_analysis": skill_timeline[-1] if skill_timeline else None
        }
    
    def get_learning_analytics(self, user_id: int) -> Dict:
        """
        Analytics for learning path progress
        
        Returns:
            {
                "active_paths": [...],
                "completed_paths": [...],
                "total_hours_invested": 120,
                "completion_rate": 0.65,
                "recommended_next_steps": [...]
            }
        """
        
        db = get_db()
        
        # Get all learning paths
        paths = db.execute(
            """SELECT path_id, target_role, status, progress_percentage, 
                      estimated_hours, hours_completed, path_data, created_at
               FROM learning_paths
               WHERE user_id = ?
               ORDER BY created_at DESC""",
            [user_id]
        ).fetchall()
        
        if not paths:
            return {
                "active_paths": [],
                "completed_paths": [],
                "total_hours_invested": 0,
                "message": "No learning paths created yet"
            }
        
        active_paths = [p for p in paths if p['status'] == 'in_progress']
        completed_paths = [p for p in paths if p['status'] == 'completed']
        
        total_hours = sum(p['hours_completed'] or 0 for p in paths)
        
        # Calculate completion rate
        if paths:
            avg_progress = sum(p['progress_percentage'] or 0 for p in paths) / len(paths)
        else:
            avg_progress = 0
        
        return {
            "active_paths": [
                {
                    "path_id": p['path_id'],
                    "role": p['target_role'],
                    "progress": p['progress_percentage'],
                    "hours_completed": p['hours_completed'],
                    "estimated_hours": p['estimated_hours']
                } for p in active_paths
            ],
            "completed_paths": [
                {
                    "path_id": p['path_id'],
                    "role": p['target_role'],
                    "completed_at": p['created_at']
                } for p in completed_paths
            ],
            "total_hours_invested": total_hours,
            "completion_rate": round(avg_progress, 1),
            "total_paths": len(paths),
            "active_count": len(active_paths),
            "completed_count": len(completed_paths)
        }
    
    def get_achievements(self, user_id: int) -> List[Dict]:
        """
        Get user achievements and milestones
        
        Returns:
            [{"title": "...", "description": "...", "earned_at": "...", "icon": "..."}, ...]
        """
        
        db = get_db()
        
        achievements = []
        
        # Check various milestones
        
        # First interview completed
        first_interview = db.execute(
            """SELECT MIN(started_at) as date FROM interview_sessions 
               WHERE user_id = ? AND status = 'completed'""",
            [user_id]
        ).fetchone()
        
        if first_interview and first_interview['date']:
            achievements.append({
                "title": "First Interview",
                "description": "Completed your first mock interview",
                "earned_at": first_interview['date'],
                "icon": "🎤",
                "category": "interview"
            })
        
        # High score achievement
        high_score = db.execute(
            """SELECT MAX(overall_score) as score, started_at FROM interview_sessions 
               WHERE user_id = ? AND status = 'completed'""",
            [user_id]
        ).fetchone()
        
        if high_score and high_score['score'] and high_score['score'] >= 90:
            achievements.append({
                "title": "Excellence",
                "description": f"Scored {high_score['score']}% in an interview",
                "earned_at": high_score['started_at'],
                "icon": "🏆",
                "category": "performance"
            })
        
        # Multiple interviews
        interview_count = db.execute(
            "SELECT COUNT(*) as count FROM interview_sessions WHERE user_id = ? AND status = 'completed'",
            [user_id]
        ).fetchone()['count']
        
        if interview_count >= 5:
            achievements.append({
                "title": "Dedicated Learner",
                "description": f"Completed {interview_count} interviews",
                "earned_at": datetime.now().isoformat(),
                "icon": "📚",
                "category": "milestone"
            })
        
        # Resume uploaded
        resume_count = db.execute(
            "SELECT COUNT(*) as count FROM resumes WHERE user_id = ?",
            [user_id]
        ).fetchone()['count']
        
        if resume_count >= 1:
            achievements.append({
                "title": "Career Ready",
                "description": "Uploaded and analyzed your resume",
                "earned_at": datetime.now().isoformat(),
                "icon": "📄",
                "category": "resume"
            })
        
        # Skill gap analysis
        skill_analysis_count = db.execute(
            "SELECT COUNT(*) as count FROM skill_gap_analysis WHERE user_id = ?",
            [user_id]
        ).fetchone()['count']
        
        if skill_analysis_count >= 1:
            achievements.append({
                "title": "Self-Aware",
                "description": "Completed skill gap analysis",
                "earned_at": datetime.now().isoformat(),
                "icon": "🧠",
                "category": "analysis"
            })
        
        return sorted(achievements, key=lambda x: x['earned_at'], reverse=True)
    
    def generate_insights(self, user_id: int) -> Dict:
        """
        Generate AI-powered insights and recommendations
        
        Returns:
            {
                "key_insights": [...],
                "recommendations": [...],
                "focus_areas": [...],
                "predicted_readiness": {...}
            }
        """
        
        # Get all user data
        dashboard = self.get_user_dashboard(user_id)
        trends = self.get_interview_trends(user_id)
        skill_progress = self.get_skill_progress(user_id)
        
        insights = []
        recommendations = []
        focus_areas = []
        
        # Analyze interview performance
        if dashboard['overview']['completed_interviews'] > 0:
            avg_score = dashboard['overview']['average_score']
            
            if avg_score >= 80:
                insights.append("🎉 Excellent interview performance! You're ready for real interviews.")
            elif avg_score >= 65:
                insights.append("👍 Good progress! A few more practice sessions will boost your confidence.")
            else:
                insights.append("📈 Keep practicing! Focus on understanding core concepts better.")
                recommendations.append("Take more mock interviews to improve your score")
        
        # Analyze trends
        if trends.get('improvement_rate', 0) > 5:
            insights.append(f"📈 Great improvement! Your scores increased by {trends['improvement_rate']}% recently.")
        elif trends.get('improvement_rate', 0) < -5:
            insights.append(f"⚠️ Scores declining. Review your weak areas and practice more.")
            recommendations.append("Review feedback from recent interviews")
        
        # Skill progress
        if skill_progress.get('skills_acquired'):
            insights.append(f"🎯 You've acquired {len(skill_progress['skills_acquired'])} new skills!")
        
        # Focus areas
        if dashboard['overview']['total_resumes'] == 0:
            focus_areas.append("Upload your resume for personalized interview questions")
        
        if dashboard['overview']['completed_interviews'] < 3:
            focus_areas.append("Complete more mock interviews to build confidence")
        
        if dashboard['overview']['skill_analyses'] == 0:
            focus_areas.append("Run skill gap analysis to identify learning priorities")
        
        return {
            "key_insights": insights if insights else ["Start your journey by uploading a resume and taking a mock interview!"],
            "recommendations": recommendations if recommendations else ["Keep up the good work!"],
            "focus_areas": focus_areas if focus_areas else ["Continue your learning path"],
            "overall_readiness": self._calculate_readiness(dashboard, trends)
        }
    
    def _calculate_readiness(self, dashboard: Dict, trends: Dict) -> Dict:
        """Calculate overall job readiness score"""
        
        score = 0
        factors = []
        
        # Interview performance (40%)
        if dashboard['overview']['completed_interviews'] > 0:
            interview_score = min(40, dashboard['overview']['average_score'] * 0.4)
            score += interview_score
            factors.append(f"Interview Performance: {dashboard['overview']['average_score']}%")
        
        # Interview count (20%)
        interview_count_score = min(20, dashboard['overview']['completed_interviews'] * 4)
        score += interview_count_score
        factors.append(f"Practice Count: {dashboard['overview']['completed_interviews']} interviews")
        
        # Improvement trend (20%)
        if trends.get('improvement_rate', 0) > 0:
            trend_score = min(20, trends['improvement_rate'] * 2)
            score += trend_score
            factors.append(f"Improvement: +{trends['improvement_rate']}%")
        
        # Resume and analysis (20%)
        if dashboard['overview']['total_resumes'] > 0:
            score += 10
            factors.append("Resume: Uploaded ✓")
        if dashboard['overview']['skill_analyses'] > 0:
            score += 10
            factors.append("Skill Analysis: Completed ✓")
        
        readiness_level = "High" if score >= 75 else "Medium" if score >= 50 else "Low"
        
        return {
            "score": round(score, 1),
            "level": readiness_level,
            "factors": factors,
            "message": self._get_readiness_message(score)
        }
    
    def _get_readiness_message(self, score: float) -> str:
        """Get readiness message based on score"""
        if score >= 80:
            return "You're highly prepared! Start applying for jobs with confidence."
        elif score >= 65:
            return "You're on the right track! A bit more practice and you'll be ready."
        elif score >= 50:
            return "Good foundation. Focus on weak areas and practice more."
        else:
            return "Keep learning! Complete more interviews and skill analyses."
