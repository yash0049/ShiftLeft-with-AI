def test_list_assets_starts_empty(client):
    response = client.get("/api/assets")
    assert response.status_code == 200
    assert response.get_json() == {"assets": []}


def test_create_asset(client):
    response = client.post(
        "/api/assets",
        json={
            "name": "db-01",
            "asset_type": "database",
            "ip_address": "10.0.0.9",
            "owner": "platform-team",
        },
    )
    assert response.status_code == 201

    body = response.get_json()
    assert body["id"] > 0
    assert body["name"] == "db-01"
    assert body["asset_type"] == "database"
    assert body["vulnerability_count"] == 0
    assert body["created_at"] is not None


def test_create_asset_defaults_type_to_other(client):
    response = client.post("/api/assets", json={"name": "mystery-box"})
    assert response.status_code == 201
    assert response.get_json()["asset_type"] == "other"


def test_create_asset_trims_whitespace(client):
    response = client.post("/api/assets", json={"name": "  padded-name  "})
    assert response.status_code == 201
    assert response.get_json()["name"] == "padded-name"


def test_create_asset_requires_name(client):
    response = client.post("/api/assets", json={"asset_type": "server"})
    assert response.status_code == 400
    assert "name" in response.get_json()["details"]


def test_create_asset_rejects_blank_name(client):
    response = client.post("/api/assets", json={"name": "   "})
    assert response.status_code == 400
    assert "name" in response.get_json()["details"]


def test_create_asset_rejects_unknown_type(client):
    response = client.post("/api/assets", json={"name": "x", "asset_type": "toaster"})
    assert response.status_code == 400
    assert "asset_type" in response.get_json()["details"]


def test_create_asset_rejects_non_json_body(client):
    response = client.post("/api/assets", data="not json", content_type="text/plain")
    assert response.status_code == 400


def test_get_asset(client, sample_asset):
    response = client.get(f"/api/assets/{sample_asset['id']}")
    assert response.status_code == 200
    assert response.get_json()["name"] == "web-01"


def test_get_missing_asset_returns_404(client):
    response = client.get("/api/assets/9999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Asset not found"


def test_update_asset(client, sample_asset):
    response = client.put(
        f"/api/assets/{sample_asset['id']}",
        json={"name": "web-01-renamed", "owner": "sec-team"},
    )
    assert response.status_code == 200

    body = response.get_json()
    assert body["name"] == "web-01-renamed"
    assert body["owner"] == "sec-team"


def test_update_asset_leaves_omitted_fields_alone(client, sample_asset):
    response = client.put(f"/api/assets/{sample_asset['id']}", json={"owner": "sec-team"})
    assert response.status_code == 200

    body = response.get_json()
    assert body["owner"] == "sec-team"
    assert body["name"] == "web-01"
    assert body["asset_type"] == "server"
    assert body["ip_address"] == "10.0.0.5"


def test_update_asset_rejects_bad_type(client, sample_asset):
    response = client.put(
        f"/api/assets/{sample_asset['id']}", json={"asset_type": "spaceship"}
    )
    assert response.status_code == 400


def test_update_missing_asset_returns_404(client):
    response = client.put("/api/assets/9999", json={"name": "ghost"})
    assert response.status_code == 404


def test_delete_asset(client, sample_asset):
    response = client.delete(f"/api/assets/{sample_asset['id']}")
    assert response.status_code == 204

    assert client.get(f"/api/assets/{sample_asset['id']}").status_code == 404


def test_delete_missing_asset_returns_404(client):
    assert client.delete("/api/assets/9999").status_code == 404


def test_deleting_asset_also_deletes_its_vulnerabilities(client, sample_vulnerability):
    asset_id = sample_vulnerability["asset_id"]

    assert client.delete(f"/api/assets/{asset_id}").status_code == 204

    remaining = client.get("/api/vulnerabilities").get_json()["vulnerabilities"]
    assert remaining == []


def test_asset_reports_vulnerability_count(client, sample_vulnerability):
    response = client.get(f"/api/assets/{sample_vulnerability['asset_id']}")
    assert response.get_json()["vulnerability_count"] == 1
