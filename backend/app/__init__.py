from flask import Flask
from flask_cors import CORS
from .database import init_db, close_db
from .error_handlers import register_error_handlers
from .hardening import setup_logging, add_security_headers, get_cors_config, validate_environment
from .routes.auth import auth_bp
from .routes.profile import profile_bp
from .routes.careers import careers_bp
from .routes.progress import progress_bp
from .routes.dashboard import dashboard_bp
from .routes.ai import ai_bp
from .routes.skillgap import skillgap_bp
from .routes.learning import learning_bp
import os
import logging


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    
    # Validate environment variables
    env_valid, missing_vars = validate_environment()
    if not env_valid:
        logging.warning(f'Missing environment variables: {", ".join(missing_vars)}')
    
    # Configure CORS based on environment
    environment = os.getenv('FLASK_ENV', 'development')
    cors_config = get_cors_config(environment)
    CORS(app, **cors_config)

    app.config.from_object("app.config.Config")

    # Setup logging
    setup_logging(app)

    with app.app_context():
        pass # Schema is already initialized
    
    # Register global error handlers
    register_error_handlers(app)
    
    # Close database connection at end of request
    app.teardown_appcontext(close_db)
    
    # Add security headers to all responses
    @app.after_request
    def after_request(response):
        return add_security_headers(response)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(careers_bp, url_prefix="/api/careers")
    app.register_blueprint(progress_bp, url_prefix="/api/progress")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(ai_bp, url_prefix="/api")
    app.register_blueprint(skillgap_bp, url_prefix="/api/skill-gap")
    app.register_blueprint(learning_bp, url_prefix="/api/learning-path")

    # Register AI routes (Production-Ready Routes)
    from app.routes.ai_routes import ai_routes_bp
    app.register_blueprint(ai_routes_bp)
    
    from app.routes.interview_routes_v2 import interview_v2_bp
    app.register_blueprint(interview_v2_bp)
    
    from app.routes.skill_gap_v2 import skill_gap_v2_bp
    app.register_blueprint(skill_gap_v2_bp)
    
    # Register Workflow routes
    from app.routes.workflow_routes import workflow_bp
    app.register_blueprint(workflow_bp)
    
    # Register Interview Insights routes (history, analytics)
    from app.routes.interview_routes import interview_bp as interview_insights_bp
    app.register_blueprint(interview_insights_bp, url_prefix="/api/interview")
    
    # Register Enhanced Interview routes (start, answer, evaluate, proctor)
    from app.routes.interview import interview_bp as interview_enhanced_bp
    app.register_blueprint(interview_enhanced_bp, url_prefix="/api/interview")
    
    # Register Skill Gap Analysis routes
    from app.routes.skill_gap import skill_gap_bp
    app.register_blueprint(skill_gap_bp)
    
    # Register Resume History routes
    from app.routes.resume_routes import resume_history_bp
    app.register_blueprint(resume_history_bp)
    
    # Register NEW Enhanced Services
    from app.routes.voice import voice_bp
    app.register_blueprint(voice_bp)
    
    from app.routes.code_eval import code_eval_bp
    app.register_blueprint(code_eval_bp)
    
    from app.routes.analytics import analytics_bp
    app.register_blueprint(analytics_bp)
    
    from app.routes.proctor import proctor_bp
    app.register_blueprint(proctor_bp)

    @app.get("/health")
    def health():
        from .hardening import check_system_health
        return check_system_health()

    app.logger.info('UpSkill AI Backend initialized successfully')
    return app
