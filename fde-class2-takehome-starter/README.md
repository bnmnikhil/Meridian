# Meridian Retail Support-Draft Review Tool

This is the completed Class 2 classroom project and the starting point for the take-home assignment.

It reads one fictional customer-support case and a fictional policy, then displays the supplied facts, policy, and a structured draft for human review. It cannot send messages, approve refunds, or change records.

## Files

- `app.py` runs the review tool.
- `policy.md` contains the fictional Meridian policy.
- `cases.json` contains the three fictional cases.
- `demo_outputs.json` contains clearly labelled offline examples.
- `setup_env.py` stores the application credential in a project-only `.env` file.
- `.env.example` shows the required variable names without containing a secret.
- `test_app.py` and `test_setup_env.py` check the expected behaviour without calling an external API.
- `TAKE_HOME_ASSIGNMENT.md` contains the complete beginner walkthrough.

## Important billing note

Live mode requires an OpenRouter API key. The default `openrouter/free` model routes to available free models, subject to OpenRouter's free-model rate limits and availability; selecting a paid model requires sufficient credits. The take-home assignment does not require a key: its new missing-information path and all automated tests work without a live model call.

Never paste an API key into chat, commit `.env`, or include `.env` in a submission.

## Setup on macOS, Linux, or Windows WSL

Open a terminal in this folder and run each command separately:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

The final test line should report that all tests passed.

## Safe commands that need no API key

```bash
python app.py --case C1 --offline-demo
python app.py --case C2
python app.py --case C4
python app.py --case C1 --simulate-timeout
```

- Offline mode uses a clearly labelled prerecorded synthetic result.
- C2 stops before the model because its delivery date is missing.
- C4 stops before the model because its order ID is missing (Policy P5).
- Simulated timeout shows the safe manual fallback.

## Optional live mode

To use live mode, create an OpenRouter API key and ensure your account can access the selected model:

```bash
python setup_env.py
python app.py --case C1
```

The key is entered using hidden input and saved only in the ignored `.env` file. If you already have a `.env` file with an older model setting, run `setup_env.py` again and confirm replacing it, or set `APP_OPENROUTER_MODEL=openrouter/free` there. The free-model router selects a free model that supports the app's structured output request. You can choose another OpenRouter model that supports structured outputs when running `setup_env.py`.

## Take-home assignment

Open [`TAKE_HOME_ASSIGNMENT.md`](TAKE_HOME_ASSIGNMENT.md) and follow it from the beginning. You may use either Claude Code or OpenCode.
