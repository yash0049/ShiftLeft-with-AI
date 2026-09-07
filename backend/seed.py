"""Populate the local database with a few sample rows.

Usage:  python seed.py
"""

from app import create_app
from app.extensions import db
from app.models import Asset, Vulnerability

ASSETS = [
    {
        "name": "web-01",
        "asset_type": "server",
        "ip_address": "10.0.0.5",
        "owner": "platform-team",
        "description": "Public nginx reverse proxy",
    },
    {
        "name": "payments-db",
        "asset_type": "database",
        "ip_address": "10.0.2.14",
        "owner": "payments-team",
        "description": "PostgreSQL primary",
    },
    {
        "name": "internal-portal",
        "asset_type": "application",
        "owner": "it-services",
        "description": "Employee self-service portal",
    },
]

VULNERABILITIES = [
    {
        "title": "SQL injection in login form",
        "severity": "critical",
        "status": "open",
        "cve_id": "CVE-2024-1234",
        "asset": "internal-portal",
        "description": "Unparameterized query in the auth handler.",
    },
    {
        "title": "Outdated OpenSSL (1.1.1n)",
        "severity": "high",
        "status": "in_progress",
        "cve_id": "CVE-2023-0286",
        "asset": "web-01",
    },
    {
        "title": "Database accepts unencrypted connections",
        "severity": "high",
        "status": "open",
        "asset": "payments-db",
    },
    {
        "title": "Missing HTTP security headers",
        "severity": "low",
        "status": "resolved",
        "asset": "web-01",
    },
    {
        "title": "Verbose error pages leak stack traces",
        "severity": "medium",
        "status": "accepted",
        "asset": "internal-portal",
    },
]


def main():
    app = create_app()
    with app.app_context():
        if Asset.query.first() or Vulnerability.query.first():
            print("Database already has data; nothing seeded.")
            return

        assets = {}
        for spec in ASSETS:
            asset = Asset(**spec)
            db.session.add(asset)
            assets[spec["name"]] = asset
        db.session.flush()

        for spec in VULNERABILITIES:
            spec = dict(spec)
            asset_name = spec.pop("asset", None)
            vuln = Vulnerability(**spec)
            if asset_name:
                vuln.asset_id = assets[asset_name].id
            db.session.add(vuln)

        db.session.commit()
        print(f"Seeded {len(ASSETS)} assets and {len(VULNERABILITIES)} vulnerabilities.")


if __name__ == "__main__":
    main()
