import sqlite3
import os
from flask import g, current_app


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=30.0,  # Wait up to 30 seconds for locks to clear
            check_same_thread=False
        )
        g.db.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys = ON")
        # Set busy timeout
        g.db.execute("PRAGMA busy_timeout = 30000")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    # Mirror the logic in config.py: use /tmp on Vercel
    db_path = os.getenv("DATABASE_PATH", "skilliq.db")
    if os.getenv("VERCEL"):
        db_path = os.path.join("/tmp", os.path.basename(db_path))
    conn = sqlite3.connect(db_path, timeout=30.0)
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            education_level TEXT,
            preferred_field TEXT,
            goals TEXT,
            learning_pace TEXT,
            language_preference TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_interests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            interest TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS student_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL,
            level TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS careers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            match_score INTEGER NOT NULL,
            demand_score INTEGER NOT NULL,
            salary_range TEXT,
            job_outlook TEXT
        );

        CREATE TABLE IF NOT EXISTS career_skill_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            career_id INTEGER REFERENCES careers(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL,
            required_level TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS progress_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            milestone TEXT NOT NULL,
            status TEXT NOT NULL,
            score_delta INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Resume Intelligence
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            resume_text TEXT NOT NULL,
            file_name TEXT,
            analysis_data TEXT,
            ats_score INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Skill Graph
        CREATE TABLE IF NOT EXISTS user_skill_graph (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL,
            skill_level TEXT NOT NULL,
            years_experience INTEGER DEFAULT 0,
            category TEXT,
            last_assessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Interview Sessions
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            level TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 5,
            type TEXT DEFAULT 'general',
            status TEXT DEFAULT 'active',
            overall_score INTEGER,
            content_score REAL,
            communication_score REAL,
            evaluation_data TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP
        );

        -- Interview Q&A
        CREATE TABLE IF NOT EXISTS interview_qa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            answer TEXT,
            question_type TEXT,
            score INTEGER,
            content_score REAL DEFAULT 0,
            communication_score REAL DEFAULT 0,
            feedback TEXT,
            asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Proctoring Logs
        CREATE TABLE IF NOT EXISTS proctor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
            event_type TEXT NOT NULL,
            severity TEXT DEFAULT 'low',
            details TEXT,
            snapshot TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Proctoring Snapshots
        CREATE TABLE IF NOT EXISTS proctor_snapshots (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
            image_data TEXT NOT NULL,
            frame_number INTEGER DEFAULT 0,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Skill Gap Analysis
        CREATE TABLE IF NOT EXISTS skill_gap_analysis (
            analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            target_role TEXT NOT NULL,
            target_level TEXT DEFAULT 'Mid-level',
            readiness_score INTEGER DEFAULT 0,
            analysis_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Learning Paths
        CREATE TABLE IF NOT EXISTS learning_paths (
            path_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            target_role TEXT NOT NULL,
            status TEXT DEFAULT 'not_started',
            progress_percentage INTEGER DEFAULT 0,
            estimated_hours INTEGER DEFAULT 0,
            hours_completed INTEGER DEFAULT 0,
            path_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Chat History
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Voice Analysis Results
        CREATE TABLE IF NOT EXISTS voice_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
            qa_id INTEGER REFERENCES interview_qa(id) ON DELETE CASCADE,
            transcript TEXT NOT NULL,
            duration_seconds REAL,
            fluency_score REAL DEFAULT 0,
            confidence_score REAL DEFAULT 0,
            clarity_score REAL DEFAULT 0,
            analysis_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Code Evaluations
        CREATE TABLE IF NOT EXISTS code_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
            qa_id INTEGER REFERENCES interview_qa(id) ON DELETE CASCADE,
            code TEXT NOT NULL,
            language TEXT NOT NULL,
            correctness_score INTEGER DEFAULT 0,
            efficiency_score INTEGER DEFAULT 0,
            quality_score INTEGER DEFAULT 0,
            evaluation_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Run migrations for existing databases (add missing columns safely)
    migrations = [
        "ALTER TABLE interview_qa ADD COLUMN content_score REAL DEFAULT 0",
        "ALTER TABLE interview_qa ADD COLUMN communication_score REAL DEFAULT 0",
        "ALTER TABLE interview_qa ADD COLUMN question_type TEXT DEFAULT 'behavioral'",
        "ALTER TABLE skill_gap_analysis ADD COLUMN gap_data TEXT",
        "ALTER TABLE learning_paths ADD COLUMN progress_percentage INTEGER DEFAULT 0",
        "ALTER TABLE resumes ADD COLUMN target_role TEXT DEFAULT ''",
    ]
    for migration in migrations:
        try:
            conn.execute(migration)
        except Exception:
            pass  # Column already exists
    conn.commit()

    # Seed careers if empty
    existing = conn.execute("SELECT COUNT(*) FROM careers").fetchone()[0]
    if existing == 0:
        conn.executescript("""
            INSERT INTO careers (title, description, match_score, demand_score, salary_range, job_outlook) VALUES
            ('AI Engineer', 'Build intelligent systems, ML solutions, and deployed AI products.', 91, 95, '₹8L - ₹18L', 'Very High'),
            ('Data Analyst', 'Translate data into insight for products, operations, and strategy.', 86, 88, '₹5L - ₹12L', 'High'),
            ('UI/UX Designer', 'Craft beautiful, research-backed digital experiences.', 78, 74, '₹6L - ₹14L', 'Growing'),
            ('Cybersecurity Analyst', 'Protect systems, investigate threats, and secure digital infrastructure.', 75, 90, '₹7L - ₹15L', 'Very High');

            INSERT INTO career_skill_map (career_id, skill_name, required_level) VALUES
            (1, 'Python', 'Advanced'), (1, 'Machine Learning', 'Intermediate'),
            (1, 'Statistics', 'Intermediate'), (1, 'Data Structures', 'Intermediate'),
            (2, 'SQL', 'Advanced'), (2, 'Python', 'Intermediate'), (2, 'Visualization', 'Intermediate'),
            (3, 'Figma', 'Advanced'), (3, 'User Research', 'Intermediate'),
            (4, 'Networking', 'Intermediate'), (4, 'Linux', 'Intermediate');
        """)
    conn.commit()
    conn.close()
