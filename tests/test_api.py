from fastapi import HTTPException
import pytest

def test_start_run_success(client):
    # 1. Create a task
    task_body = {
        "goal": "follow up with Acme",
        "scenario": "send_followup",
        "autonomy": "autonomous",
        "expected_effects": [
            {"tool": "send_message", "match": {"contact_id": "c_1"}}
        ]
    }
    task_resp = client.post("/api/v1/tasks", json=task_body)
    assert task_resp.status_code == 200
    task_id = task_resp.json()["id"]

    # 2. Start a run for that task
    run_body = {"task_id": task_id}
    run_resp = client.post("/api/v1/runs", json=run_body)

    # We expect this to fail with 501 until implemented
    assert run_resp.status_code == 201
    run_data = run_resp.json()
    assert run_data["status"] == "completed"
    assert len(run_data.get("effects", [])) >= 1

def test_start_run_not_found(client):
    # Start a run for a non-existent task
    run_body = {"task_id": "non_existent_task_id"}
    run_resp = client.post("/api/v1/runs", json=run_body)

    assert run_resp.status_code == 404
