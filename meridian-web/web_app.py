import os
import sys
import json
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


def execute_case_review(case_id: str) -> tuple[str, dict[str, str], dict[str, Any]]:
    """Delegate one selected case to the core and return display context."""
    task_path, context_directory = configured_paths()
    _, sources = review_app.load_context_pack(task_path, context_directory)
    case, policy = review_app.load_inputs(case_id)
    result = review_app.get_case_task_result(case, policy, sources)
    task, prepared_sources, _ = review_app.prepare_case_context(case, policy, sources)
    return task, prepared_sources, result


def context_overview() -> tuple[str, dict[str, str]]:
    task_path, context_directory = configured_paths()
    task, sources = review_app.load_context_pack(task_path, context_directory)
    return task, sources


def source_preview_context(task: str, sources: dict[str, str]) -> dict[str, Any]:
    task_path, _ = configured_paths()
    return {
        "task": task,
        "source_names": sorted(sources),
        "source_contents": {task_path.name: task, **sources},
        "preview_file_name": task_path.name,
    }


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
        "source_contents": {},
        "preview_file_name": "task.md",
        "result": None,
        "error": None,
    }
    context.update(overrides)
    return context


@app.get("/")
def index():
    try:
        task, sources = context_overview()
        selected_case_id = requested_case_id()
        return render_template("index.html", **page_context(
            **source_preview_context(task, sources),
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
            **source_preview_context(task, sources),
            result=result,
            selected_case_id=selected_case_id,
        ))
    except Exception as exc:
        app.logger.exception("Context-pack review failed")
        try:
            task, sources = context_overview()
            source_context = source_preview_context(task, sources)
        except Exception:
            source_context = source_preview_context("", {})
        return render_template("index.html", **page_context(
            **source_context,
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
