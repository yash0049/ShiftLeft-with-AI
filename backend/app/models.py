from datetime import datetime, timezone

from .extensions import db

ASSET_TYPES = ("server", "workstation", "database", "application", "network", "other")
SEVERITIES = ("critical", "high", "medium", "low", "info")
VULN_STATUSES = ("open", "in_progress", "resolved", "accepted")


def _utcnow():
    return datetime.now(timezone.utc)


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    asset_type = db.Column(db.String(40), nullable=False, default="other")
    ip_address = db.Column(db.String(45))
    owner = db.Column(db.String(120))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    vulnerabilities = db.relationship(
        "Vulnerability",
        back_populates="asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "asset_type": self.asset_type,
            "ip_address": self.ip_address,
            "owner": self.owner,
            "description": self.description,
            "vulnerability_count": len(self.vulnerabilities),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Vulnerability(db.Model):
    __tablename__ = "vulnerabilities"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    severity = db.Column(db.String(20), nullable=False, default="medium")
    status = db.Column(db.String(20), nullable=False, default="open")
    cve_id = db.Column(db.String(40))
    description = db.Column(db.Text)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id", ondelete="CASCADE"), nullable=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    asset = db.relationship("Asset", back_populates="vulnerabilities")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "status": self.status,
            "cve_id": self.cve_id,
            "description": self.description,
            "asset_id": self.asset_id,
            "asset_name": self.asset.name if self.asset else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
