from flask import Blueprint, request

from ..extensions import db
from ..errors import ValidationError
from ..models import SEVERITIES, VULN_STATUSES, Asset, Vulnerability
from ..validation import clean_string, get_json_body

bp = Blueprint("vulnerabilities", __name__, url_prefix="/api/vulnerabilities")


def _parse_asset_id(body, errors):
    """Validate an optional asset_id, confirming the asset exists."""
    asset_id = body.get("asset_id")
    if asset_id is None or asset_id == "":
        return None

    if isinstance(asset_id, bool):
        errors["asset_id"] = "Must be an integer asset id"
        return None

    if not isinstance(asset_id, int):
        try:
            asset_id = int(asset_id)
        except (TypeError, ValueError):
            errors["asset_id"] = "Must be an integer asset id"
            return None

    if db.session.get(Asset, asset_id) is None:
        errors["asset_id"] = f"No asset with id {asset_id}"
        return None

    return asset_id


def _parse_vulnerability(body, *, partial=False):
    errors = {}
    data = {}

    if not partial or "title" in body:
        data["title"] = clean_string(
            body.get("title"), "title", errors, required=True, max_length=200
        )

    for field, allowed, default in (
        ("severity", SEVERITIES, "medium"),
        ("status", VULN_STATUSES, "open"),
    ):
        if not partial or field in body:
            value = clean_string(body.get(field), field, errors, allowed=allowed)
            if value is not None or not partial:
                data[field] = value or default

    for field, max_length in (("cve_id", 40), ("description", 5000)):
        if not partial or field in body:
            data[field] = clean_string(body.get(field), field, errors, max_length=max_length)

    if not partial or "asset_id" in body:
        data["asset_id"] = _parse_asset_id(body, errors)

    if errors:
        raise ValidationError(errors)
    return data


@bp.get("")
def list_vulnerabilities():
    query = Vulnerability.query

    severity = request.args.get("severity")
    if severity:
        query = query.filter(Vulnerability.severity == severity.strip().lower())

    status = request.args.get("status")
    if status:
        query = query.filter(Vulnerability.status == status.strip().lower())

    asset_id = request.args.get("asset_id", type=int)
    if asset_id is not None:
        query = query.filter(Vulnerability.asset_id == asset_id)

    vulns = query.order_by(Vulnerability.created_at.desc()).all()
    return {"vulnerabilities": [v.to_dict() for v in vulns]}


@bp.get("/<int:vuln_id>")
def get_vulnerability(vuln_id):
    vuln = db.get_or_404(Vulnerability, vuln_id, description="Vulnerability not found")
    return vuln.to_dict()


@bp.post("")
def create_vulnerability():
    data = _parse_vulnerability(get_json_body(request))
    vuln = Vulnerability(**data)
    db.session.add(vuln)
    db.session.commit()
    return vuln.to_dict(), 201


@bp.put("/<int:vuln_id>")
def update_vulnerability(vuln_id):
    vuln = db.get_or_404(Vulnerability, vuln_id, description="Vulnerability not found")
    data = _parse_vulnerability(get_json_body(request), partial=True)
    for field, value in data.items():
        setattr(vuln, field, value)
    db.session.commit()
    return vuln.to_dict()


@bp.delete("/<int:vuln_id>")
def delete_vulnerability(vuln_id):
    vuln = db.get_or_404(Vulnerability, vuln_id, description="Vulnerability not found")
    db.session.delete(vuln)
    db.session.commit()
    return "", 204
