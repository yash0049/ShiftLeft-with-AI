import pytest

from app import create_app
from app.extensions import db as _db
from app.models import Asset, Vulnerability


@pytest.fixture
def app():
    """A Flask app backed by a throwaway in-memory SQLite database."""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    yield app
    with app.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db


@pytest.fixture
def sample_asset(app):
    with app.app_context():
        asset = Asset(name="web-01", asset_type="server", ip_address="10.0.0.5")
        _db.session.add(asset)
        _db.session.commit()
        return asset.to_dict()


@pytest.fixture
def sample_vulnerability(app, sample_asset):
    with app.app_context():
        vuln = Vulnerability(
            title="Outdated OpenSSL",
            severity="high",
            status="open",
            cve_id="CVE-2024-0001",
            asset_id=sample_asset["id"],
        )
        _db.session.add(vuln)
        _db.session.commit()
        return vuln.to_dict()
