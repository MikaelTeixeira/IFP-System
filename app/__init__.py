from flask import Flask
from markupsafe import Markup, escape
import re

from .config import Config


def create_app(config_object=Config):
    """Create and configure the Instituto Fabiana Pinto application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    from .database import init_database
    init_database(app)

    from .core import core_bp
    from .auth import auth_bp
    from .academic import academic_bp
    from .questions import questions_bp
    from .assessments import assessments_bp
    from .curriculum import curriculum_bp
    from .student import student_bp
    from .materials import materials_bp
    from .users import users_bp
    from .reports import reports_bp
    from .scanner import scanner_bp
    from .errors import register_error_handlers
    from .auth.security import current_profile
    from .navigation import build_navigation

    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(academic_bp, url_prefix="/academico")
    app.register_blueprint(questions_bp, url_prefix="/questoes")
    app.register_blueprint(assessments_bp, url_prefix="/simulados")
    app.register_blueprint(curriculum_bp, url_prefix="/curriculo")
    app.register_blueprint(student_bp, url_prefix="/aluno")
    app.register_blueprint(materials_bp, url_prefix="/materiais")
    app.register_blueprint(users_bp, url_prefix="/usuarios")
    app.register_blueprint(reports_bp, url_prefix="/relatorios")
    app.register_blueprint(scanner_bp, url_prefix="/cartoes-resposta")
    register_error_handlers(app)

    @app.context_processor
    def inject_application_context():
        profile = current_profile()
        unread_notifications = 0
        if profile:
            from .data.notifications import unread_count
            unread_notifications = unread_count(profile)
        return {
            "current_profile": profile,
            "navigation_items": build_navigation(profile),
            "unread_notifications": unread_notifications,
        }

    @app.template_filter("question_text")
    def question_text(value):
        safe_text = str(escape(value or ""))
        formatted = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe_text)
        return Markup(formatted.replace("\n", "<br>"))

    return app
