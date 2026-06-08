import os
from pathlib import Path

os.environ["DATABASE_URL"] = f"sqlite:///{Path(__file__).with_name('test.db')}"
os.environ["GROQ_API_KEY"] = ""

from fastapi.testclient import TestClient

from app.main import app


def test_agent_tools_end_to_end():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json()["database"] is True

        hcps = client.get("/hcps")
        assert hcps.status_code == 200
        hcp_id = hcps.json()[0]["id"]

        logged = client.post(
            "/interactions",
            json={
                "hcp_id": hcp_id,
                "channel": "In person",
                "interaction_type": "Detailing",
                "raw_notes": "Discussed access support. HCP asked for follow-up and approved evidence.",
                "products": ["CardioFlow"],
                "topics": ["access", "evidence"],
            },
        )
        assert logged.status_code == 200
        interaction = logged.json()["result"]["interaction"]
        assert interaction["call_quality_score"] > 0

        for tool in [
            "get_hcp_profile",
            "suggest_next_best_action",
            "draft_follow_up",
            "compliance_review",
        ]:
            response = client.post(f"/agent/tools/{tool}", json={"hcp_id": hcp_id, "payload": {}})
            assert response.status_code == 200
            assert response.json()["tool_name"] == tool

        edited = client.patch(
            f"/interactions/{interaction['id']}",
            json={"sentiment": "Interested", "commitments": ["Send approved access sheet"]},
        )
        assert edited.status_code == 200
        assert edited.json()["result"]["interaction"]["sentiment"] == "Interested"
