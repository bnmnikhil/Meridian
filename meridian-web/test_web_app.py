import web_app


VALID_WEB_RESULT = {
    "case_id": "C2",
    "case_summary": "Delivery date is missing.",
    "known_facts": [
        {"field": "order_id", "value": "MR-1088", "source_id": "order_record:MR-1088"}
    ],
    "evidence_refs": ["P2", "P4"],
    "evidence_links": [
        {
            "claim": "The delivery date is required.",
            "source_id": "policy_register:policy.md",
        }
    ],
    "missing_information": ["delivery_date"],
    "conflicting_information": [],
    "draft_reply": "Please provide the delivery date.",
    "review_status": "NEEDS_INFORMATION",
    "human_action_required": "Confirm the delivery date.",
}


def test_home_page_loads_context_pack():
    client = web_app.app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"Meridian Review Console" in response.data
    assert b"evidence_map.json" in response.data
    for case_id in (b"C1", b"C2", b"C3", b"C4"):
        assert f'value="{case_id.decode()}"'.encode() in response.data
    assert b"loading-panel" in response.data
    assert b"static/app.js" in response.data


def test_health_endpoint_reports_loaded_context():
    client = web_app.app.test_client()
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert response.get_json()["context_sources"] > 0
    assert response.get_json()["available_cases"] == ["C1", "C2", "C3", "C4"]


def test_run_page_renders_validated_result(monkeypatch):
    monkeypatch.setattr(
        web_app,
        "execute_case_review",
        lambda case_id: ("Task", {"cases.json": "{}"}, VALID_WEB_RESULT),
    )
    client = web_app.app.test_client()

    response = client.post("/run", data={"case_id": "C2"})

    assert response.status_code == 200
    assert b"NEEDS INFORMATION" in response.data
    assert b"Please provide the delivery date." in response.data
    assert b"order_record:MR-1088" in response.data


def test_api_run_returns_result(monkeypatch):
    monkeypatch.setattr(
        web_app,
        "execute_case_review",
        lambda case_id: ("Task", {"cases.json": "{}"}, VALID_WEB_RESULT),
    )
    client = web_app.app.test_client()

    response = client.post("/api/run", json={"case_id": "C2"})

    assert response.status_code == 200
    assert response.get_json()["result"] == VALID_WEB_RESULT
    assert response.get_json()["case_id"] == "C2"


def test_missing_order_case_is_resolved_without_a_model_call(monkeypatch):
    def model_must_not_run(task, sources):
        raise AssertionError("Model was called for a case with no order ID")

    monkeypatch.setattr(web_app.review_app, "get_task_result", model_must_not_run)

    _, _, result = web_app.execute_case_review("C4")

    assert result["review_status"] == "NEEDS_INFORMATION"
    assert result["missing_information"] == ["order_id"]


def test_unknown_case_is_rejected():
    client = web_app.app.test_client()
    response = client.post("/api/run", json={"case_id": "C99"})

    assert response.status_code == 502
    assert "Unknown case" in response.get_json()["error"]
