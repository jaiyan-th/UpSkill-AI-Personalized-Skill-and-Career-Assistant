"""
Smart Proctoring Service
Monitors interview integrity with webcam, tab switching, and suspicious activity detection
"""

import base64
import json
from datetime import datetime
from typing import Dict, List
from app.database import get_db

class ProctorService:
    def __init__(self):
        self.violation_weights = {
            'tab_switch': 5,
            'window_blur': 3,
            'no_face_detected': 8,
            'multiple_faces': 10,
            'looking_away': 4,
            'suspicious_activity': 7,
            'copy_paste_attempt': 10
        }
    
    def log_event(
        self, 
        session_id: int,
        event_type: str,
        details: Dict = None,
        snapshot: str = None
    ) -> Dict:
        """
        Log proctoring event
        
        Args:
            session_id: Interview session ID
            event_type: Type of event (tab_switch, no_face, etc.)
            details: Additional event details
            snapshot: Base64 encoded image snapshot
        
        Returns:
            {
                "logged": True,
                "event_id": 123,
                "severity": "high/medium/low"
            }
        """
        
        db = get_db()
        
        severity = self._calculate_severity(event_type)
        details_json = json.dumps(details) if details else None
        
        cursor = db.execute(
            """INSERT INTO proctor_logs 
               (session_id, event_type, severity, details, snapshot, timestamp)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            [session_id, event_type, severity, details_json, snapshot]
        )
        db.commit()
        
        return {
            "logged": True,
            "event_id": cursor.lastrowid,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
    
    def save_snapshot(self, session_id: int, image_data: str, frame_number: int) -> Dict:
        """
        Save webcam snapshot
        
        Args:
            session_id: Interview session ID
            image_data: Base64 encoded image
            frame_number: Frame sequence number
        
        Returns:
            {"saved": True, "snapshot_id": 123}
        """
        
        db = get_db()
        
        cursor = db.execute(
            """INSERT INTO proctor_snapshots 
               (session_id, image_data, frame_number, captured_at)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
            [session_id, image_data, frame_number]
        )
        db.commit()
        
        return {
            "saved": True,
            "snapshot_id": cursor.lastrowid,
            "frame_number": frame_number
        }
    
    def analyze_session_integrity(self, session_id: int) -> Dict:
        """
        Analyze overall session integrity
        
        Returns:
            {
                "integrity_score": 0-100,
                "total_violations": 15,
                "violation_breakdown": {...},
                "risk_level": "low/medium/high",
                "suspicious_periods": [...],
                "recommendations": [...]
            }
        """
        
        db = get_db()
        
        # Get all events for session
        events = db.execute(
            """SELECT event_type, severity, details, timestamp 
               FROM proctor_logs 
               WHERE session_id = ?
               ORDER BY timestamp""",
            [session_id]
        ).fetchall()
        
        if not events:
            return {
                "integrity_score": 100,
                "total_violations": 0,
                "violation_breakdown": {},
                "risk_level": "low",
                "suspicious_periods": [],
                "recommendations": ["No violations detected. Good session integrity."]
            }
        
        # Count violations by type
        violation_breakdown = {}
        total_penalty = 0
        
        for event in events:
            event_type = event['event_type']
            violation_breakdown[event_type] = violation_breakdown.get(event_type, 0) + 1
            total_penalty += self.violation_weights.get(event_type, 5)
        
        # Calculate integrity score (start at 100, deduct for violations)
        integrity_score = max(0, 100 - total_penalty)
        
        # Determine risk level
        if integrity_score >= 80:
            risk_level = "low"
        elif integrity_score >= 60:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Identify suspicious periods (clusters of violations)
        suspicious_periods = self._identify_suspicious_periods(events)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(violation_breakdown, risk_level)
        
        return {
            "integrity_score": integrity_score,
            "total_violations": len(events),
            "violation_breakdown": violation_breakdown,
            "risk_level": risk_level,
            "suspicious_periods": suspicious_periods,
            "recommendations": recommendations,
            "timeline": [
                {
                    "timestamp": e['timestamp'],
                    "event": e['event_type'],
                    "severity": e['severity']
                } for e in events
            ]
        }
    
    def _calculate_severity(self, event_type: str) -> str:
        """Calculate severity level for event type"""
        weight = self.violation_weights.get(event_type, 5)
        
        if weight >= 8:
            return "high"
        elif weight >= 5:
            return "medium"
        else:
            return "low"
    
    def _identify_suspicious_periods(self, events: List) -> List[Dict]:
        """
        Identify time periods with clustered violations
        
        Returns:
            [{"start": "...", "end": "...", "violation_count": 5, "types": [...]}, ...]
        """
        
        if len(events) < 3:
            return []
        
        suspicious = []
        window_size = 3  # Look for 3+ violations within short time
        
        for i in range(len(events) - window_size + 1):
            window = events[i:i+window_size]
            
            # Check if violations are within 2 minutes of each other
            start_time = datetime.fromisoformat(window[0]['timestamp'])
            end_time = datetime.fromisoformat(window[-1]['timestamp'])
            duration = (end_time - start_time).total_seconds()
            
            if duration <= 120:  # 2 minutes
                suspicious.append({
                    "start": window[0]['timestamp'],
                    "end": window[-1]['timestamp'],
                    "duration_seconds": duration,
                    "violation_count": len(window),
                    "types": [e['event_type'] for e in window]
                })
        
        return suspicious
    
    def _generate_recommendations(self, violations: Dict, risk_level: str) -> List[str]:
        """Generate recommendations based on violations"""
        
        recommendations = []
        
        if risk_level == "high":
            recommendations.append("⚠️ High risk detected. Manual review strongly recommended.")
        elif risk_level == "medium":
            recommendations.append("⚠️ Moderate concerns. Consider follow-up interview.")
        else:
            recommendations.append("✅ Good session integrity. No major concerns.")
        
        # Specific recommendations
        if violations.get('tab_switch', 0) > 5:
            recommendations.append(f"Frequent tab switching detected ({violations['tab_switch']} times). Candidate may have been looking up answers.")
        
        if violations.get('no_face_detected', 0) > 3:
            recommendations.append(f"Face not detected multiple times ({violations['no_face_detected']}). Candidate may have left the interview.")
        
        if violations.get('multiple_faces', 0) > 0:
            recommendations.append(f"Multiple faces detected ({violations['multiple_faces']} times). Someone else may have been present.")
        
        if violations.get('copy_paste_attempt', 0) > 0:
            recommendations.append(f"Copy-paste attempts detected ({violations['copy_paste_attempt']} times). Candidate may have tried to paste external code.")
        
        if violations.get('looking_away', 0) > 10:
            recommendations.append(f"Frequently looking away from screen ({violations['looking_away']} times). May indicate distraction or external help.")
        
        return recommendations
    
    def get_session_snapshots(self, session_id: int, limit: int = 10) -> List[Dict]:
        """
        Get webcam snapshots for session
        
        Returns:
            [{"snapshot_id": 1, "frame_number": 5, "captured_at": "...", "image_data": "..."}, ...]
        """
        
        db = get_db()
        
        snapshots = db.execute(
            """SELECT snapshot_id, frame_number, captured_at, image_data
               FROM proctor_snapshots
               WHERE session_id = ?
               ORDER BY frame_number DESC
               LIMIT ?""",
            [session_id, limit]
        ).fetchall()
        
        return [
            {
                "snapshot_id": s['snapshot_id'],
                "frame_number": s['frame_number'],
                "captured_at": s['captured_at'],
                "image_data": s['image_data'][:100] + "..." if s['image_data'] else None  # Truncate for response
            } for s in snapshots
        ]
    
    def detect_face_in_snapshot(self, image_data: str) -> Dict:
        """
        Detect face presence in snapshot (placeholder for actual face detection)
        In production, integrate with face detection API (AWS Rekognition, Azure Face API, etc.)
        
        Returns:
            {
                "face_detected": True,
                "face_count": 1,
                "confidence": 0.95,
                "looking_at_camera": True
            }
        """
        
        # Placeholder implementation
        # In production, use actual face detection API
        
        return {
            "face_detected": True,
            "face_count": 1,
            "confidence": 0.85,
            "looking_at_camera": True,
            "note": "Using placeholder face detection. Integrate with AWS Rekognition or Azure Face API for production."
        }
    
    def generate_integrity_report(self, session_id: int) -> Dict:
        """
        Generate comprehensive integrity report for session
        
        Returns:
            Complete report with analysis, snapshots, timeline, and recommendations
        """
        
        integrity = self.analyze_session_integrity(session_id)
        snapshots = self.get_session_snapshots(session_id, limit=5)
        
        db = get_db()
        session = db.execute(
            """SELECT role, level, started_at, completed_at, status
               FROM interview_sessions
               WHERE session_id = ?""",
            [session_id]
        ).fetchone()
        
        return {
            "session_id": session_id,
            "session_info": {
                "role": session['role'] if session else "Unknown",
                "level": session['level'] if session else "Unknown",
                "started_at": session['started_at'] if session else None,
                "completed_at": session['completed_at'] if session else None,
                "status": session['status'] if session else "Unknown"
            },
            "integrity_analysis": integrity,
            "sample_snapshots": snapshots,
            "generated_at": datetime.now().isoformat()
        }
