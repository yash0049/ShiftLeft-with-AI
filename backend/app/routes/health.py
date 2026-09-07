from flask import Blueprint
from sqlalchemy import text

from ..extensions import db

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    """Liveness plus a real database round-trip."""
    try:
        db.session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "unavailable"
        return {"status": "degraded", "database": database}, 503

    return {"status": "ok", "database": database}
