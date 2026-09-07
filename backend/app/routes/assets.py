from flask import Blueprint, request

from ..extensions import db
from ..errors import ValidationError
from ..models import ASSET_TYPES, Asset
from ..validation import clean_string, get_json_body

bp = Blueprint("assets", __name__, url_prefix="/api/assets")


def _parse_asset(body, *, partial=False):
    """Build a dict of validated asset fields.

    With partial=True (PUT), only the keys actually present in the body are
    returned, so an update never blanks out fields the client left alone.
    """
    errors = {}
    data = {}

    if not partial or "name" in body:
        data["name"] = clean_string(
            body.get("name"), "name", errors, required=True, max_length=120
        )

    if not partial or "asset_type" in body:
        asset_type = clean_string(
            body.get("asset_type"), "asset_type", errors, allowed=ASSET_TYPES
        )
        if asset_type is not None or not partial:
            data["asset_type"] = asset_type or "other"

    for field, max_length in (("ip_address", 45), ("owner", 120), ("description", 2000)):
        if not partial or field in body:
            data[field] = clean_string(body.get(field), field, errors, max_length=max_length)

    if errors:
        raise ValidationError(errors)
    return data


@bp.get("")
def list_assets():
    assets = Asset.query.order_by(Asset.created_at.desc()).all()
    return {"assets": [a.to_dict() for a in assets]}


@bp.get("/<int:asset_id>")
def get_asset(asset_id):
    asset = db.get_or_404(Asset, asset_id, description="Asset not found")
    return asset.to_dict()


@bp.post("")
def create_asset():
    data = _parse_asset(get_json_body(request))
    asset = Asset(**data)
    db.session.add(asset)
    db.session.commit()
    return asset.to_dict(), 201


@bp.put("/<int:asset_id>")
def update_asset(asset_id):
    asset = db.get_or_404(Asset, asset_id, description="Asset not found")
    data = _parse_asset(get_json_body(request), partial=True)
    for field, value in data.items():
        setattr(asset, field, value)
    db.session.commit()
    return asset.to_dict()


@bp.delete("/<int:asset_id>")
def delete_asset(asset_id):
    asset = db.get_or_404(Asset, asset_id, description="Asset not found")
    db.session.delete(asset)
    db.session.commit()
    return "", 204
