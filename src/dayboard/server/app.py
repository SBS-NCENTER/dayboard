"""Flask App Factory."""

from pathlib import Path

from flask import Flask

from .. import config

_STATIC = (Path(__file__).resolve().parent / ".." / "static").resolve()


def create_app() -> Flask:
    config.ensure_runtime_dirs()
    app = Flask(__name__, static_folder=str(_STATIC), static_url_path="/static")
    from .routes.api import bp as api_bp
    from .routes.views import bp as views_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp)
    return app
