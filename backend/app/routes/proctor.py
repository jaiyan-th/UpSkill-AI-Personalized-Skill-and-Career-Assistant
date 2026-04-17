"""
Proctoring API Routes
Handles webcam monitoring, event logging, and integrity analysis
"""

from flask import Blueprint, request, jsonify
from app.auth_utils import require_auth
from app.services.proctor_service import ProctorService

proctor_bp = Blueprint('proctor', __name__, url_prefix='/api/proctor')
proctor_service = ProctorService()

@proctor_bp.route('/log-event', methods=['POST'])
@require_auth
def log_event(current_user):
    """
    Log proctoring event
    
    Request:
        {
            "session_id": 123,
            "event_type": "tab_switch",
            "details": {...},
            "snapshot": "base64_image_data"
        }
    
    Response:
        {
            "success": true,
            "event_id": 456,
            "severity": "medium"
        }
    """
    try:
        data = request.json or {}
        
        session_id = data.get('session_id')
        event_type = data.get('event_type')
        details = data.get('details')
        snapshot = data.get('snapshot')
        
        if not session_id or not event_type:
            return jsonify({
                "success": False,
                "error": "session_id and event_type are required"
            }), 400
        
        result = proctor_service.log_event(
            session_id=session_id,
            event_type=event_type,
            details=details,
            snapshot=snapshot
        )
        
        return jsonify({
            "success": True,
            **result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@proctor_bp.route('/save-snapshot', methods=['POST'])
@require_auth
def save_snapshot(current_user):
    """
    Save webcam snapshot
    
    Request:
        {
            "session_id": 123,
            "image_data": "base64_encoded_image",
            "frame_number": 5
        }
    
    Response:
        {
            "success": true,
            "snapshot_id": 789
        }
    """
    try:
        data = request.json or {}
        
        session_id = data.get('session_id')
        image_data = data.get('image_data')
        frame_number = data.get('frame_number', 0)
        
        if not session_id or not image_data:
            return jsonify({
                "success": False,
                "error": "session_id and image_data are required"
            }), 400
        
        result = proctor_service.save_snapshot(
            session_id=session_id,
            image_data=image_data,
            frame_number=frame_number
        )
        
        return jsonify({
            "success": True,
            **result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@proctor_bp.route('/integrity/<int:session_id>', methods=['GET'])
@require_auth
def get_integrity(current_user, session_id):
    """
    Get session integrity analysis
    
    Response:
        {
            "success": true,
            "integrity": {
                "integrity_score": 85,
                "total_violations": 5,
                "risk_level": "low",
                "recommendations": [...]
            }
        }
    """
    try:
        integrity = proctor_service.analyze_session_integrity(session_id)
        
        return jsonify({
            "success": True,
            "integrity": integrity
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@proctor_bp.route('/snapshots/<int:session_id>', methods=['GET'])
@require_auth
def get_snapshots(current_user, session_id):
    """
    Get webcam snapshots for session
    
    Query params:
        limit: Number of snapshots to return (default: 10)
    
    Response:
        {
            "success": true,
            "snapshots": [...]
        }
    """
    try:
        limit = int(request.args.get('limit', 10))
        snapshots = proctor_service.get_session_snapshots(session_id, limit)
        
        return jsonify({
            "success": True,
            "snapshots": snapshots,
            "count": len(snapshots)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@proctor_bp.route('/report/<int:session_id>', methods=['GET'])
@require_auth
def get_report(current_user, session_id):
    """
    Get comprehensive integrity report
    
    Response:
        {
            "success": true,
            "report": {
                "session_info": {...},
                "integrity_analysis": {...},
                "sample_snapshots": [...]
            }
        }
    """
    try:
        report = proctor_service.generate_integrity_report(session_id)
        
        return jsonify({
            "success": True,
            "report": report
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@proctor_bp.route('/detect-face', methods=['POST'])
@require_auth
def detect_face(current_user):
    """
    Detect face in snapshot (placeholder for actual face detection)
    
    Request:
        {
            "image_data": "base64_encoded_image"
        }
    
    Response:
        {
            "success": true,
            "face_detected": true,
            "face_count": 1,
            "confidence": 0.95
        }
    """
    try:
        data = request.json or {}
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({
                "success": False,
                "error": "image_data is required"
            }), 400
        
        result = proctor_service.detect_face_in_snapshot(image_data)
        
        return jsonify({
            "success": True,
            **result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
