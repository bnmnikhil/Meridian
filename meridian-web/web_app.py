import os
import sys
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

WEB_ROOT = Path(__file__).resolve().parent
CORE_ROOT = Path(
    os.getenv("MERIDIAN_CORE_DIR", WEB_ROOT.parent / "fde-class2-takehome-starter")
).resolve()
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

import app as review_app  # noqa: E402 - core path is configured immediately above

app = Flask(__name__)


def configured_paths() -> tuple[Path, Path | None]:
    task_path = Path(os.getenv("APP_TASK_PATH", CORE_ROOT / "task.md"))
    context_value = os.getenv("APP_CONTEXT_DIR")
    context_directory = Path(context_value) if context_value else None
    return task_path, context_directory


def case_options() -> list[dict[str, str]]:
    cases_path = CORE_ROOT / "cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    return [
        {
            "case_id": case_id,
            "label": f"{case_id} · {case.get('product') or 'Unknown product'}",
        }
        for case_id, case in sorted(cases.items())
    ]


def policy_rules(policy: str) -> dict[str, str]:
    rules: dict[str, str] = {}
    for line in policy.splitlines():
        match = re.match(r"^(P\d+)\.\s*(.+)$", line.strip())
        if match:
            rules[match.group(1)] = match.group(2)
    return rules


def case_evidence_map(case: dict[str, Any], policy: str) -> dict[str, dict[str, Any]]:
    case_id = case["case_id"]
    order_label = case.get("order_id") or case_id
    return {
        f"support_queue:{case_id}": {
            "source_file": "cases.json",
            "record_path": case_id,
            "data": {
                "case_id": case_id,
                "product": case.get("product"),
                "customer_question": case.get("customer_question"),
            },
        },
        f"order_record:{order_label}": {
            "source_file": "cases.json",
            "record_path": case_id,
            "data": {
                "case_id": case_id,
                "order_id": case.get("order_id"),
                "product": case.get("product"),
                "delivery_date": case.get("delivery_date"),
            },
        },
        f"issue_record:{case_id}": {
            "source_file": "cases.json",
            "record_path": case_id,
            "data": {
                "case_id": case_id,
                "issue_status": case.get("issue_status"),
                "issue_details": case.get("issue_details"),
            },
        },
        "policy_register:policy.md": {
            "source_file": "policy.md",
            "record_path": None,
            "data": policy_rules(policy),
        },
    }


def known_facts(case: dict[str, Any], evidence_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    case_id = case["case_id"]
    order_label = case.get("order_id") or case_id
    source_fields = [
        (f"support_queue:{case_id}", ("case_id", "product", "customer_question")),
        (f"order_record:{order_label}", ("order_id", "delivery_date")),
        (f"issue_record:{case_id}", ("issue_status", "issue_details")),
    ]
    facts: list[dict[str, Any]] = []
    for source_id, fields in source_fields:
        data = evidence_map[source_id]["data"]
        for field in fields:
            if data.get(field) is not None:
                facts.append({"field": field, "value": data[field], "source_id": source_id})
    return facts


def local_gate_result(
    case: dict[str, Any],
    evidence_map: dict[str, dict[str, Any]],
    now: datetime | None = None,
) -> dict[str, Any] | None:
    case_id = case["case_id"]
    order_label = case.get("order_id") or case_id
    support_source = f"support_queue:{case_id}"
    order_source = f"order_record:{order_label}"
    policy_source = "policy_register:policy.md"
    facts = known_facts(case, evidence_map)
    summary = f"{case.get('product') or 'Product'} support request for case {case_id}."

    if not case.get("order_id"):
        return {
            "case_id": case_id,
            "case_summary": f"{summary} The order ID is missing.",
            "known_facts": facts,
            "evidence_refs": ["P5", "P4"],
            "evidence_links": [
                {"claim": "The order ID is missing.", "source_id": order_source},
                {"claim": "An order ID is required before drafting.", "source_id": policy_source},
            ],
            "missing_information": ["order_id"],
            "conflicting_information": [],
            "draft_reply": review_app.missing_order_id_result()["draft_reply"],
            "review_status": "NEEDS_INFORMATION",
            "human_action_required": "Confirm the order ID before the review continues.",
        }

    if not case.get("delivery_date"):
        return {
            "case_id": case_id,
            "case_summary": f"{summary} The delivery date is missing.",
            "known_facts": facts,
            "evidence_refs": ["P2", "P4"],
            "evidence_links": [
                {"claim": "The delivery date is missing.", "source_id": order_source},
                {"claim": "The delivery date is required to apply the 78-hour rule.", "source_id": policy_source},
            ],
            "missing_information": ["delivery_date"],
            "conflicting_information": [],
            "draft_reply": review_app.missing_delivery_date_result()["draft_reply"],
            "review_status": "NEEDS_INFORMATION",
            "human_action_required": "Confirm the delivery date before the review continues.",
        }

    current_timestamp = now or datetime.now(timezone.utc)
    delivery_timestamp = review_app.parse_delivery_timestamp(case["delivery_date"])
    if delivery_timestamp < current_timestamp - review_app.REFUND_WINDOW:
        issue_source = f"issue_record:{case_id}"
        return {
            "case_id": case_id,
            "case_summary": f"{summary} The supplied delivery date is outside the 78-hour window.",
            "known_facts": facts,
            "evidence_refs": ["P1", "P3", "P4"],
            "evidence_links": [
                {"claim": "The supplied delivery date is outside the 78-hour window.", "source_id": order_source},
                {"claim": "The issue remains open.", "source_id": issue_source},
                {"claim": "Requests after 78 hours are outside policy.", "source_id": policy_source},
            ],
            "missing_information": [],
            "conflicting_information": [],
            "draft_reply": review_app.out_of_policy_result()["draft_reply"],
            "review_status": "BLOCKED",
            "human_action_required": "A human reviewer confirms the delivery timestamp and policy cutoff.",
        }
    return None


def build_case_task(case: dict[str, Any], evidence_map: dict[str, dict[str, Any]]) -> str:
    source_ids = list(evidence_map)
    evidence = ", ".join(f"`{source_id}`" for source_id in source_ids)
    return f"""# Task

Prepare a structured case review and draft for a human reviewer.

## Evidence

{evidence} only.

## Boundaries

No return approval, refund, customer message, record change or invented fact.

## Output contract

Use the supplied output contract definitions and preserve evidence source IDs.

## Human-review requirement

A person reviews the proposed draft before any dependent action continues.
"""


def execute_case_review(case_id: str) -> tuple[str, dict[str, str], dict[str, Any]]:
    """Run one selected case, applying local gates before any model call."""
    task_path, context_directory = configured_paths()
    _, sources = review_app.load_context_pack(task_path, context_directory)
    case, policy = review_app.load_inputs(case_id)
    evidence_map = case_evidence_map(case, policy)
    sources["evidence_map.json"] = json.dumps(evidence_map, indent=2)
    task = build_case_task(case, evidence_map)
    result = local_gate_result(case, evidence_map)
    if result is None:
        result = review_app.get_task_result(task, sources)
    else:
        review_app.validate_task_result(
            result,
            set(evidence_map),
            evidence_map,
            set(result["missing_information"]),
            case_id,
        )
    return task, sources, result


def context_overview() -> tuple[str, list[str]]:
    task_path, context_directory = configured_paths()
    task, sources = review_app.load_context_pack(task_path, context_directory)
    return task, sorted(sources)


def requested_case_id() -> str:
    if request.is_json:
        value = (request.get_json(silent=True) or {}).get("case_id")
    else:
        value = request.form.get("case_id") or request.args.get("case")
    selected = value or "C2"
    available = {option["case_id"] for option in case_options()}
    if selected not in available:
        raise ValueError(f"Unknown case {selected!r}. Available cases: {sorted(available)}")
    return selected


def page_context(**overrides: Any) -> dict[str, Any]:
    context: dict[str, Any] = {
        "case_options": case_options(),
        "selected_case_id": "C2",
        "task": "",
        "source_names": [],
        "result": None,
        "error": None,
    }
    context.update(overrides)
    return context


@app.get("/")
def index():
    try:
        task, source_names = context_overview()
        selected_case_id = requested_case_id()
        return render_template("index.html", **page_context(
            task=task,
            source_names=source_names,
            selected_case_id=selected_case_id,
        ))
    except Exception as exc:
        app.logger.exception("Unable to load the context pack")
        return render_template("index.html", **page_context(
            error=f"Unable to load the context pack: {exc}",
        )), 500


@app.post("/run")
def run_review():
    try:
        selected_case_id = requested_case_id()
        task, sources, result = execute_case_review(selected_case_id)
        return render_template("index.html", **page_context(
            task=task,
            source_names=sorted(sources),
            result=result,
            selected_case_id=selected_case_id,
        ))
    except Exception as exc:
        app.logger.exception("Context-pack review failed")
        try:
            task, source_names = context_overview()
        except Exception:
            task, source_names = "", []
        return render_template("index.html", **page_context(
            task=task,
            source_names=source_names,
            selected_case_id=request.form.get("case_id") or "C2",
            error=f"The review could not be completed: {exc}",
        )), 502


@app.get("/api/health")
def health():
    try:
        _, sources = context_overview()
        return jsonify({
            "status": "ok",
            "context_sources": len(sources),
            "available_cases": [option["case_id"] for option in case_options()],
        })
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500


@app.post("/api/run")
def api_run():
    try:
        selected_case_id = requested_case_id()
        _, sources, result = execute_case_review(selected_case_id)
        return jsonify({
            "case_id": selected_case_id,
            "result": result,
            "context_sources": sorted(sources),
        })
    except Exception as exc:
        app.logger.exception("Context-pack API review failed")
        return jsonify({"error": str(exc)}), 502


if __name__ == "__main__":
    host = os.getenv("WEB_HOST", "127.0.0.1")
    port = int(os.getenv("WEB_PORT", "8080"))
    app.run(host=host, port=port, debug=False)
