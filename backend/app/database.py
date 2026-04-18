import psycopg2
from psycopg2.extras import DictCursor
import os
from flask import g, current_app


class PostgresCursorWrapper:
    """Wrapper around psycopg2 cursor to emulate sqlite3 cursor behavior"""
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def execute(self, query, params=None):
        # Convert SQLite '?' parameters to PostgreSQL '%s'
        if params is not None:
            query = query.replace('?', '%s')
            
        # Automatically handle .lastrowid for INSERT statements
        is_insert = query.strip().upper().startswith('INSERT')
        if is_insert and 'RETURNING' not in query.upper():
            query = query.rstrip().rstrip(';') + ' RETURNING id;'
            
        self._cursor.execute(query, params)
        
        if is_insert:
            returned = self._cursor.fetchone()
            if returned and 'id' in returned:
                self.lastrowid = returned['id']
                
        return self

    def fetchone(self):
        return self._cursor.fetchone()
        
    def fetchall(self):
        return self._cursor.fetchall()
        
    def fetchmany(self, size):
        return self._cursor.fetchmany(size)
        
    @property
    def description(self):
        return self._cursor.description
        
    def __iter__(self):
        return iter(self._cursor)


class PostgresConnection:
    """Wrapper to make psycopg2 connection behave like sqlite3 connection."""
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=None):
        cursor = self.conn.cursor(cursor_factory=DictCursor)
        wrapper = PostgresCursorWrapper(cursor)
        wrapper.execute(query, params)
        return wrapper

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def rollback(self):
        self.conn.rollback()


def get_db():
    if "db" not in g:
        # Use DictCursor to support both index and key access (like sqlite3.Row)
        conn = psycopg2.connect(current_app.config["SUPABASE_DB_URL"])
        g.db = PostgresConnection(conn)
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db_path = current_app.config.get("SUPABASE_DB_URL")
    if not db_path:
        db_path = "postgresql://postgres:postgres@localhost:5432/upskill"
        
    conn = psycopg2.connect(db_path)
    cursor = conn.cursor()
    
    # PostgreSQL Schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            education_level TEXT,
            preferred_field TEXT,
            goals TEXT,
            learning_pace TEXT,
            language_preference TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_interests (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            interest TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS student_skills (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL,
            level TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS careers (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            match_score INTEGER NOT NULL,
            demand_score INTEGER NOT NULL,
            salary_range TEXT,
            job_outlook TEXT
        );

        CREATE TABLE IF NOT EXISTS career_skill_map (
            id SERIAL PRIMARY KEY,
            career_id INTEGER REFERENCES careers(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL,
            required_level TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS progress_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            milestone TEXT NOT NULL,
            status TEXT NOT NULL,
            score_delta INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Resume Intelligence
        CREATE TABLE IF NOT EXISTS resumes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            resume_text TEXT NOT NULL,
            file_name TEXT,
            analysis_data TEXT,
            ats_score INTEGER,
            target_role TEXT DEFAULT '',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Skill Graph
        CREATE TABLE IF NOT EXISTS user_skill_graph (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL,
            skill_level TEXT NOT NULL,
            years_experience INTEGER DEFAULT 0,
            category TEXT,
            last_assessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Interview Sessions
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            answer TEXT,
            question_type TEXT DEFAULT 'behavioral',
            score INTEGER,
            content_score REAL DEFAULT 0,
            communication_score REAL DEFAULT 0,
            feedback TEXT,
            asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Proctoring Logs
        CREATE TABLE IF NOT EXISTS proctor_logs (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
            event_type TEXT NOT NULL,
            severity TEXT DEFAULT 'low',
            details TEXT,
            snapshot TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Proctoring Snapshots
        CREATE TABLE IF NOT EXISTS proctor_snapshots (
            snapshot_id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
            image_data TEXT NOT NULL,
            frame_number INTEGER DEFAULT 0,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Skill Gap Analysis
        CREATE TABLE IF NOT EXISTS skill_gap_analysis (
            analysis_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            target_role TEXT NOT NULL,
            target_level TEXT DEFAULT 'Mid-level',
            readiness_score INTEGER DEFAULT 0,
            analysis_data TEXT NOT NULL,
            gap_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Learning Paths
        CREATE TABLE IF NOT EXISTS learning_paths (
            path_id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Voice Analysis Results
        CREATE TABLE IF NOT EXISTS voice_analyses (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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

    # Seed careers if empty
    cursor.execute("SELECT COUNT(*) FROM careers")
    existing = cursor.fetchone()[0]
    if existing == 0:
        cursor.execute("""
            INSERT INTO careers (title, description, match_score, demand_score, salary_range, job_outlook) VALUES
            ('AI Engineer', 'Build intelligent systems, ML solutions, and deployed AI products.', 91, 95, '₹8L - ₹18L', 'Very High'),
            ('Data Analyst', 'Translate data into insight for products, operations, and strategy.', 86, 88, '₹5L - ₹12L', 'High'),
            ('UI/UX Designer', 'Craft beautiful, research-backed digital experiences.', 78, 74, '₹6L - ₹14L', 'Growing'),
            ('Cybersecurity Analyst', 'Protect systems, investigate threats, and secure digital infrastructure.', 75, 90, '₹7L - ₹15L', 'Very High');
        """)
        cursor.execute("""
            INSERT INTO career_skill_map (career_id, skill_name, required_level) VALUES
            (1, 'Python', 'Advanced'), (1, 'Machine Learning', 'Intermediate'),
            (1, 'Statistics', 'Intermediate'), (1, 'Data Structures', 'Intermediate'),
            (2, 'SQL', 'Advanced'), (2, 'Python', 'Intermediate'), (2, 'Visualization', 'Intermediate'),
            (3, 'Figma', 'Advanced'), (3, 'User Research', 'Intermediate'),
            (4, 'Networking', 'Intermediate'), (4, 'Linux', 'Intermediate');
        """)
        
    conn.commit()
    cursor.close()
    conn.close()
