def test_list_vulnerabilities_starts_empty(client):
    response = client.get("/api/vulnerabilities")
    assert response.status_code == 200
    assert response.get_json() == {"vulnerabilities": []}


def test_create_vulnerability(client, sample_asset):
    response = client.post(
        "/api/vulnerabilities",
        json={
            "title": "SQL injection in login form",
            "severity": "critical",
            "cve_id": "CVE-2024-1234",
            "asset_id": sample_asset["id"],
        },
    )
    assert response.status_code == 201

    body = response.get_json()
    assert body["title"] == "SQL injection in login form"
    assert body["severity"] == "critical"
    assert body["status"] == "open"
    assert body["asset_id"] == sample_asset["id"]
    assert body["asset_name"] == "web-01"


def test_create_vulnerability_defaults(client):
    response = client.post("/api/vulnerabilities", json={"title": "Unpatched host"})
    assert response.status_code == 201

    body = response.get_json()
    assert body["severity"] == "medium"
    assert body["status"] == "open"
    assert body["asset_id"] is None
    assert body["asset_name"] is None


def test_create_vulnerability_normalizes_case(client):
    response = client.post(
        "/api/vulnerabilities", json={"title": "Weak TLS", "severity": "HIGH"}
    )
    assert response.status_code == 201
    assert response.get_json()["severity"] == "high"


def test_create_vulnerability_requires_title(client):
    response = client.post("/api/vulnerabilities", json={"severity": "low"})
    assert response.status_code == 400
    assert "title" in response.get_json()["details"]


def test_create_vulnerability_rejects_unknown_severity(client):
    response = client.post(
        "/api/vulnerabilities", json={"title": "x", "severity": "apocalyptic"}
    )
    assert response.status_code == 400
    assert "severity" in response.get_json()["details"]


def test_create_vulnerability_rejects_unknown_status(client):
    response = client.post("/api/vulnerabilities", json={"title": "x", "status": "maybe"})
    assert response.status_code == 400
    assert "status" in response.get_json()["details"]


def test_create_vulnerability_rejects_missing_asset(client):
    response = client.post("/api/vulnerabilities", json={"title": "x", "asset_id": 4242})
    assert response.status_code == 400
    assert "asset_id" in response.get_json()["details"]


def test_create_vulnerability_reports_all_errors_at_once(client):
    response = client.post(
        "/api/vulnerabilities", json={"severity": "nope", "status": "nope"}
    )
    assert response.status_code == 400

    details = response.get_json()["details"]
    assert set(details) == {"title", "severity", "status"}


def test_get_vulnerability(client, sample_vulnerability):
    response = client.get(f"/api/vulnerabilities/{sample_vulnerability['id']}")
    assert response.status_code == 200
    assert response.get_json()["title"] == "Outdated OpenSSL"


def test_get_missing_vulnerability_returns_404(client):
    response = client.get("/api/vulnerabilities/9999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Vulnerability not found"


def test_update_vulnerability_status(client, sample_vulnerability):
    response = client.put(
        f"/api/vulnerabilities/{sample_vulnerability['id']}", json={"status": "resolved"}
    )
    assert response.status_code == 200

    body = response.get_json()
    assert body["status"] == "resolved"
    assert body["title"] == "Outdated OpenSSL"
    assert body["severity"] == "high"


def test_update_vulnerability_can_unassign_asset(client, sample_vulnerability):
    response = client.put(
        f"/api/vulnerabilities/{sample_vulnerability['id']}", json={"asset_id": None}
    )
    assert response.status_code == 200
    assert response.get_json()["asset_id"] is None


def test_update_missing_vulnerability_returns_404(client):
    response = client.put("/api/vulnerabilities/9999", json={"status": "resolved"})
    assert response.status_code == 404


def test_delete_vulnerability(client, sample_vulnerability):
    response = client.delete(f"/api/vulnerabilities/{sample_vulnerability['id']}")
    assert response.status_code == 204

    assert client.get(f"/api/vulnerabilities/{sample_vulnerability['id']}").status_code == 404


def test_delete_missing_vulnerability_returns_404(client):
    assert client.delete("/api/vulnerabilities/9999").status_code == 404


def test_filter_by_severity(client):
    client.post("/api/vulnerabilities", json={"title": "a", "severity": "low"})
    client.post("/api/vulnerabilities", json={"title": "b", "severity": "critical"})

    response = client.get("/api/vulnerabilities?severity=critical")
    vulns = response.get_json()["vulnerabilities"]
    assert [v["title"] for v in vulns] == ["b"]


def test_filter_by_status(client):
    client.post("/api/vulnerabilities", json={"title": "a", "status": "open"})
    client.post("/api/vulnerabilities", json={"title": "b", "status": "resolved"})

    response = client.get("/api/vulnerabilities?status=resolved")
    vulns = response.get_json()["vulnerabilities"]
    assert [v["title"] for v in vulns] == ["b"]


def test_filter_by_asset(client, sample_vulnerability):
    client.post("/api/vulnerabilities", json={"title": "unassigned"})

    response = client.get(f"/api/vulnerabilities?asset_id={sample_vulnerability['asset_id']}")
    vulns = response.get_json()["vulnerabilities"]
    assert [v["title"] for v in vulns] == ["Outdated OpenSSL"]
