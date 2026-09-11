from flask import Flask

from .config import Config


def create_app(config_object=Config):
    """Create and configure the Instituto Fabiana Pinto application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    from .core import core_bp
    from .errors import register_error_handlers

    app.register_blueprint(core_bp)
    register_error_handlers(app)

    return app

