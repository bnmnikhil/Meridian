# Meridian Core

The core reads a fictional retail-support case and policy, applies local safety
checks, and prepares a structured draft for human review. It cannot send
messages, approve refunds, or modify records.

Every result contains the case summary, sourced facts, policy references,
evidence links, missing or conflicting information, proposed reply, review
status, and next human action.

The policy uses a two-day delivery rule. Because the records contain a date but
no delivery time, the implementation uses a 78-hour date-only allowance. A
human reviewer must confirm the actual timestamp before acting.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1`.

## Run

Run the configured task:

```bash
python app.py
```

Run a selected case:

```bash
python app.py --case C2
```

Run a prerecorded example without an API key:

```bash
python app.py --case C1 --offline-demo
```

For live model calls, run `python setup_env.py` and then select a case. The key
is stored in the ignored project `.env` file. Never commit that file.

See [`TAKE_HOME_ASSIGNMENT.md`](TAKE_HOME_ASSIGNMENT.md) for the assignment
instructions.
