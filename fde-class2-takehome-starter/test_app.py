import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import app


VALID_RESULT = {
    "draft_reply": (
        "The damaged jacket can be referred for human return review. "
        "This is not a refund approval, and the issue remains open."
    ),
    "evidence_refs": ["P1", "P3", "P4"],
    "missing_information": [],
    "review_status": "READY_FOR_HUMAN_REVIEW",
}
VALID_JSON = json.dumps(VALID_RESULT)


def good_model_call(case, policy):
    return dict(VALID_RESULT)


VALID_TASK_RESULT = {
    "case_id": "C1",
    "case_summary": "A supplied case summary.",
    "known_facts": [{"field": "order_id", "value": "MR-1042", "source_id": "S1"}],
    "evidence_refs": ["P1"],
    "evidence_links": [{"claim": "The order ID is MR-1042.", "source_id": "S1"}],
    "missing_information": [],
    "conflicting_information": [],
    "draft_reply": "Proposed wording for human review.",
    "review_status": "READY_FOR_HUMAN_REVIEW",
    "human_action_required": "Review the proposed reply.",
}


def test_all_cases_and_policy_load():
    for case_id in ("C1", "C2", "C3", "C4"):
        case, policy = app.load_inputs(case_id)
        assert case["case_id"] == case_id
        for policy_id in ("P1", "P2", "P3", "P4", "P5"):
            assert policy_id in policy


def test_unknown_case_is_rejected():
    with pytest.raises(KeyError):
        app.load_inputs("C99")


def test_context_pack_loads_supported_files_and_ignores_runtime_folders(tmp_path):
    task_path = tmp_path / "task.md"
    task_path.write_text("Prepare the result.", encoding="utf-8")
    (tmp_path / "information.md").write_text("Supplied information", encoding="utf-8")
    (tmp_path / "records.json").write_text('{"case_id": "C1"}', encoding="utf-8")
    (tmp_path / "notes.txt").write_text("Additional notes", encoding="utf-8")
    (tmp_path / "ignored.py").write_text("secret = True", encoding="utf-8")
    ignored_directory = tmp_path / ".venv"
    ignored_directory.mkdir()
    (ignored_directory / "secret.md").write_text("Do not load", encoding="utf-8")

    task, sources = app.load_context_pack(task_path)

    assert task == "Prepare the result."
    assert sources == {
        "information.md": "Supplied information",
        "notes.txt": "Additional notes",
        "records.json": '{"case_id": "C1"}',
    }


def test_context_pack_rejects_an_empty_task(tmp_path):
    task_path = tmp_path / "task.md"
    task_path.write_text("", encoding="utf-8")
    (tmp_path / "information.md").write_text("Supplied information", encoding="utf-8")

    with pytest.raises(ValueError, match="Task file is empty"):
        app.load_context_pack(task_path)


def test_task_prompt_labels_every_context_source():
    system_prompt, user_prompt = app.build_task_prompts(
        "Prepare the result.",
        {"facts.md": "Facts", "records/case.json": '{"case_id": "C1"}'},
    )

    assert "using only the supplied context pack" in system_prompt
    assert "TASK\nPrepare the result." in user_prompt
    assert "--- CONTEXT FILE: facts.md ---\nFacts" in user_prompt
    assert "--- CONTEXT FILE: records/case.json ---" in user_prompt


def test_evidence_map_and_requested_ids_are_validated():
    sources = {
        "cases.json": '{"C2": {}}',
        "policy.md": "P2",
        "evidence_map.json": json.dumps(
            {
                "support_queue:C2": {
                    "source_file": "cases.json",
                    "record_path": "C2",
                    "data": {"case_id": "C2"},
                },
                "policy_register:policy.md": {
                    "source_file": "policy.md",
                    "record_path": None,
                    "data": {"P2": "Delivery date required."},
                },
            }
        ),
    }
    task = """# Task

## Evidence

`support_queue:C2` and `policy_register:policy.md` only.
"""

    evidence_map = app.load_evidence_map(sources)
    assert app.requested_evidence_ids(task) == [
        "support_queue:C2",
        "policy_register:policy.md",
    ]
    assert set(evidence_map) == {"support_queue:C2", "policy_register:policy.md"}


def test_requested_missing_fields_excludes_review_status_tokens():
    task = """# Task

## Missing-information behaviour

Name `delivery_date` and set `NEEDS_INFORMATION`.
"""
    assert app.requested_missing_fields(task) == ["delivery_date"]


def test_task_result_contract_is_validated():
    assert app.parse_task_result(json.dumps(VALID_TASK_RESULT)) == VALID_TASK_RESULT

    invalid = {**VALID_TASK_RESULT, "review_status": "UNAVAILABLE"}
    with pytest.raises(ValueError, match="unsupported"):
        app.validate_task_result(invalid)

    with pytest.raises(ValueError, match="outside the evidence map"):
        app.validate_task_result(VALID_TASK_RESULT, {"S2"})


def test_task_result_rejects_a_known_fact_not_supported_by_its_source():
    evidence_map = {
        "S1": {
            "source_file": "facts.md",
            "record_path": None,
            "data": {"order_id": "MR-9999"},
        },
        "policy_register:policy.md": {
            "source_file": "policy.md",
            "record_path": None,
            "data": {"P1": "Policy text"},
        },
    }

    with pytest.raises(ValueError, match="not supported"):
        app.validate_task_result(
            VALID_TASK_RESULT,
            {"S1", "policy_register:policy.md"},
            evidence_map,
        )


def test_c1_uses_model_result():
    case, policy = app.load_inputs("C1")
    result = app.review_case(
        case,
        policy,
        model_call=good_model_call,
        current_timestamp=datetime(2026, 9, 15, 5, 59, tzinfo=timezone.utc),
    )
    assert result["review_status"] == "READY_FOR_HUMAN_REVIEW"


def test_delivery_older_than_78_hours_is_blocked_before_model_call():
    case, policy = app.load_inputs("C1")

    def model_must_not_run(case, policy):
        raise AssertionError("The model was called for an out-of-policy delivery")

    result = app.review_case(
        case,
        policy,
        model_call=model_must_not_run,
        current_timestamp=datetime(2026, 9, 15, 6, 0, 1, tzinfo=timezone.utc),
    )

    assert result["review_status"] == "BLOCKED"
    assert result["missing_information"] == []
    assert result["evidence_refs"] == ["P1", "P4"]
    assert "outside Meridian Retail's 78-hour refund window" in result["draft_reply"]


def test_delivery_at_exactly_78_hours_is_still_eligible_for_review():
    case, policy = app.load_inputs("C1")
    result = app.review_case(
        case,
        policy,
        model_call=good_model_call,
        current_timestamp=datetime(2026, 9, 15, 6, tzinfo=timezone.utc),
    )
    assert result["review_status"] == "READY_FOR_HUMAN_REVIEW"


def test_c2_stops_before_model_call():
    case, policy = app.load_inputs("C2")

    def model_must_not_run(case, policy):
        raise AssertionError("The model was called even though delivery_date is missing")

    result = app.review_case(case, policy, model_call=model_must_not_run)
    assert result["review_status"] == "NEEDS_INFORMATION"
    assert result["missing_information"] == ["delivery_date"]
    assert result["evidence_refs"] == ["P2", "P4"]


def test_c4_stops_before_model_call():
    case, policy = app.load_inputs("C4")

    def model_must_not_run(case, policy):
        raise AssertionError("The model was called even though order_id is missing")

    result = app.review_case(case, policy, model_call=model_must_not_run)
    assert result["review_status"] == "NEEDS_INFORMATION"
    assert result["missing_information"] == ["order_id"]
    assert result["evidence_refs"] == ["P5", "P4"]


def test_timeout_is_visible_and_safe():
    case, policy = app.load_inputs("C1")
    result = app.review_case(case, policy, simulate_timeout=True)
    assert result["review_status"] == "UNAVAILABLE"
    assert result["draft_reply"] == ""
    assert "manual review" in result["error"]


def test_provider_failure_is_visible_and_safe():
    case, policy = app.load_inputs("C1")

    def failed_model_call(case, policy):
        raise RuntimeError("provider unavailable")

    result = app.review_case(
        case,
        policy,
        model_call=failed_model_call,
        current_timestamp=datetime(2026, 9, 15, 5, 59, tzinfo=timezone.utc),
    )
    assert result["review_status"] == "UNAVAILABLE"
    assert result["draft_reply"] == ""


def test_each_failure_returns_a_new_result_object():
    first = app.unavailable_result()
    second = app.unavailable_result()
    first["missing_information"].append("changed")
    assert first is not second
    assert second["missing_information"] == []


def test_plain_json_is_unchanged():
    assert app.strip_code_fence(VALID_JSON) == VALID_JSON


def test_get_live_result_strips_markdown_code_fence():
    fenced = "```json\n" + VALID_JSON + "\n```"
    assert app.parse_model_result(fenced) == VALID_RESULT


def test_plain_code_fence_is_stripped():
    fenced = "```\n" + VALID_JSON + "\n```"
    assert app.parse_model_result(fenced) == VALID_RESULT


def test_surrounding_whitespace_is_ignored():
    assert app.parse_model_result(" \n" + VALID_JSON + "\n ") == VALID_RESULT


@pytest.mark.parametrize(
    "bad_text",
    [
        "not json",
        json.dumps({"draft_reply": "missing fields"}),
        json.dumps({**VALID_RESULT, "extra": "not allowed"}),
        json.dumps({**VALID_RESULT, "evidence_refs": "P1"}),
        json.dumps({**VALID_RESULT, "review_status": "SENT_TO_CUSTOMER"}),
    ],
)
def test_invalid_model_output_is_rejected(bad_text):
    with pytest.raises((json.JSONDecodeError, ValueError)):
        app.parse_model_result(bad_text)


def test_empty_model_response_is_rejected():
    completion = SimpleNamespace(choices=[])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kwargs: completion
    )))
    with pytest.raises(ValueError, match="no usable text"):
        app.query_model(client, "model", "system", "user")


def test_truncated_model_response_is_rejected():
    choice = SimpleNamespace(message=SimpleNamespace(content=VALID_JSON), finish_reason="length")
    completion = SimpleNamespace(choices=[choice])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kwargs: completion
    )))
    with pytest.raises(ValueError, match="cut off"):
        app.query_model(client, "model", "system", "user")


def test_query_model_requests_structured_output():
    captured = {}
    choice = SimpleNamespace(message=SimpleNamespace(content=VALID_JSON), finish_reason="stop")
    completion = SimpleNamespace(choices=[choice])

    def fake_create(**kwargs):
        captured.update(kwargs)
        return completion

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create)))
    assert app.query_model(client, "model", "system", "user") == VALID_JSON
    assert captured["model"] == "model"
    assert captured["max_tokens"] == app.DEFAULT_MAX_OUTPUT_TOKENS
    assert captured["messages"] == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "user"},
    ]
    assert captured["response_format"] == {
        "type": "json_schema",
        "json_schema": {"name": "support_draft", "strict": True, "schema": app.RESULT_SCHEMA},
    }
    assert captured["extra_body"] == {"provider": {"require_parameters": True}}


def test_task_query_uses_the_larger_output_limit(monkeypatch):
    captured = {}

    def fake_query_model(client, model, system_prompt, user_prompt, **kwargs):
        captured.update(kwargs)
        return json.dumps(VALID_TASK_RESULT)

    monkeypatch.setattr(app, "query_model", fake_query_model)
    monkeypatch.setattr(app, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("APP_OPENROUTER_API_KEY", "test-openrouter-key")

    task = """# Task

## Evidence

    `S1` and `policy_register:policy.md` only.
"""
    sources = {
        "facts.md": "Facts",
        "policy.md": "P1. Policy text",
        "evidence_map.json": json.dumps(
            {
                "S1": {
                    "source_file": "facts.md",
                    "record_path": None,
                    "data": {"case_id": "C1", "order_id": "MR-1042"},
                },
                "policy_register:policy.md": {
                    "source_file": "policy.md",
                    "record_path": None,
                    "data": {"P1": "Policy text"},
                },
            }
        ),
    }
    assert app.get_task_result(task, sources) == VALID_TASK_RESULT
    assert captured["max_output_tokens"] == app.TASK_MAX_OUTPUT_TOKENS


def test_live_result_uses_openrouter_client_and_settings(monkeypatch):
    import openai

    captured = {}
    request = {}
    choice = SimpleNamespace(message=SimpleNamespace(content=VALID_JSON), finish_reason="stop")

    def fake_create(**kwargs):
        request.update(kwargs)
        return SimpleNamespace(choices=[choice])

    def fake_client(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=fake_create
        )))

    monkeypatch.setattr(openai, "OpenAI", fake_client)
    monkeypatch.setattr(app, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("APP_OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.delenv("APP_OPENROUTER_MODEL", raising=False)

    assert app.get_live_result({"case_id": "C1"}, "P1") == VALID_RESULT
    assert request["model"] == "openrouter/free"
    assert captured == {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "test-openrouter-key",
        "timeout": 20.0,
        "max_retries": 0,
    }


def test_offline_outputs_are_valid():
    for case_id in ("C1", "C2", "C3"):
        result = app.load_offline_demo(case_id)
        assert result["review_status"] in app.ALLOWED_REVIEW_STATUSES
