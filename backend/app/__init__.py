import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from sqlalchemy import event
from sqlalchemy.engine import Engine

from .errors import register_error_handlers
from .extensions import db

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "securetrack.db"


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores FOREIGN KEY constraints unless asked, per connection."""
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app(config=None):
    app = Flask(__name__)

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
    )
    if config:
        app.config.update(config)

    CORS(
        app,
        resources={r"/api/*": {"origins": _allowed_origins()}},
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    db.init_app(app)
    register_error_handlers(app)

    from .routes.assets import bp as assets_bp
    from .routes.health import bp as health_bp
    from .routes.vulnerabilities import bp as vulnerabilities_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(vulnerabilities_bp)

    with app.app_context():
        from . import models  # noqa: F401  (register models before create_all)

        db.create_all()

    return app


def _allowed_origins():
    origins = os.environ.get("CORS_ORIGINS")
    if origins:
        return [o.strip() for o in origins.split(",") if o.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]
