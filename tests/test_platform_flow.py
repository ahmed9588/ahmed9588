import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_end_to_end_governed_flow() -> None:
    sample = json.loads(Path("docs/sample_blueprint.json").read_text())

    create_resp = client.post("/api/v1/blueprints", json={"blueprint": sample})
    assert create_resp.status_code == 200
    blueprint_id = create_resp.json()["blueprint_id"]

    approve_resp = client.post(
        f"/api/v1/blueprints/{blueprint_id}/approve",
        json={"reviewer_id": "reviewer-1"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["approval_status"] == "approved"

    generate_resp = client.post(f"/api/v1/blueprints/{blueprint_id}/generate", json={})
    assert generate_resp.status_code == 200
    tool_id = generate_resp.json()["tool_id"]

    test_resp = client.post(f"/api/v1/tools/{tool_id}/test", json={"pass_threshold": 0.8})
    assert test_resp.status_code == 200
    assert test_resp.json()["status"] == "tested"

    publish_resp = client.post(
        f"/api/v1/tools/{tool_id}/publish",
        json={"published_by": "publisher-1"},
    )
    assert publish_resp.status_code == 200

    monitoring = client.get("/api/v1/monitoring/snapshot")
    assert monitoring.status_code == 200
    body = monitoring.json()
    assert body["counts"]["publications"] >= 1
    assert body["metrics"]["tools_published"] >= 1
