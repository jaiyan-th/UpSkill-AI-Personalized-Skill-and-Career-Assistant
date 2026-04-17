from flask import Blueprint, request, jsonify
from app.database import get_db
from app.auth_utils import require_auth

progress_bp = Blueprint("progress", __name__)


@progress_bp.get("/")
@require_auth
def get_progress():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM progress_logs WHERE user_id = ? ORDER BY created_at DESC",
        [request.user["id"]],
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@progress_bp.post("/")
@require_auth
def add_progress():
    data = request.get_json()
    db = get_db()
    cur = db.execute(
        "INSERT INTO progress_logs (user_id, milestone, status, score_delta) VALUES (?, ?, ?, ?)",
        [request.user["id"], data.get("milestone"), data.get("status"), data.get("score_delta", 0)],
    )
    db.commit()
    row = db.execute("SELECT * FROM progress_logs WHERE id = ?", [cur.lastrowid]).fetchone()
    return jsonify(dict(row)), 201
