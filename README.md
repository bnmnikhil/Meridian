# Meridian

Meridian is a human-in-the-loop retail support review application. It reads a
task and its local context pack, builds evidence-backed structured output, and
exposes the same workflow through both a Python CLI and a small Flask web app.

The application drafts review results only. It does not send customer messages,
approve refunds, or update external systems.

Live application: [meridian.bonamnikhilbabu.in](https://meridian.bonamnikhilbabu.in)

## Repository layout

```text
Meridian/
|-- fde-class2-takehome-starter/  # Core task runner, context pack, and tests
|   |-- app.py                    # CLI and policy/contract enforcement
|   |-- task.md                   # Task executed when no --case is supplied
|   |-- contractDefinations.md    # Required structured-output contract
|   |-- evidence_map.json         # Evidence-to-output traceability map
|   |-- cases.json                # Synthetic review cases C1-C4
|   `-- policy.md                 # Fictional refund policy
`-- meridian-web/                 # Flask UI and deployment configuration
    |-- web_app.py
    |-- templates/ and static/
    `-- deploy/                   # systemd and Caddy configuration
```

## What it does

- Loads `task.md` and the relevant Markdown/JSON context files from the context
  folder.
- Produces output that conforms to the contract in
  `contractDefinations.md`.
- Uses `evidence_map.json` to keep conclusions traceable to supplied evidence.
- Supports synthetic cases C1-C4 in the CLI and browser UI.
- Applies a 78-hour date-only allowance for the policy's two-day rule because
  the supplied delivery records do not contain a delivery time; a human must
  confirm the actual timestamp before acting.
- Stops safely when required facts are missing or the model provider is
  unavailable.

## Local setup

Python 3.13 is recommended. From the repository root in PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\meridian-web\requirements.txt
```

The web requirements include the packages needed by the core application.

Copy the example environment file only when live model calls are needed:

```powershell
Copy-Item .\fde-class2-takehome-starter\.env.example `
  .\fde-class2-takehome-starter\.env
```

Then set `APP_OPENROUTER_API_KEY` in the local `.env`. Never commit that file.
The safe validation paths and test suite do not require an API key.

## Run the CLI

Run the current `task.md` against its context pack:

```powershell
python .\fde-class2-takehome-starter\app.py
```

Run a specific case:

```powershell
python .\fde-class2-takehome-starter\app.py --case C4
```

Other useful safe paths:

```powershell
python .\fde-class2-takehome-starter\app.py --case C1 --offline-demo
python .\fde-class2-takehome-starter\app.py --case C1 --simulate-timeout
```

## Run the web application

```powershell
Set-Location .\meridian-web
waitress-serve --host=127.0.0.1 --port=8081 web_app:app
```

Open `http://127.0.0.1:8081`. The service also exposes:

- `GET /api/health`
- `POST /api/run` with form field `case_id=C1`, `C2`, `C3`, or `C4`

The web app reads the sibling `fde-class2-takehome-starter` folder by default.
Set `MERIDIAN_CORE_DIR` to override that location.

## Tests

From the repository root:

```powershell
python -m json.tool .\fde-class2-takehome-starter\cases.json > $null
python -m pytest -q .\fde-class2-takehome-starter .\meridian-web
```

## Deployment

The deployed architecture keeps Waitress private on `127.0.0.1:8081` and uses
Caddy as the public TLS reverse proxy. Deployment assets are under
`meridian-web/deploy/`:

- `meridian-review.service` defines the hardened systemd service.
- `Caddyfile` terminates HTTPS and proxies requests to Waitress.

The public app is intentionally a review interface. Before exposing live paid
model calls broadly, protect it with authentication or an access gateway and
apply request rate limits.

## Security

- `.env`, virtual environments, caches, IDE metadata, logs, and private keys
  are ignored at the repository level.
- `.env.example` documents variable names but contains no credential.
- Case data in this repository is synthetic.
- Model failures return a safe manual-review response instead of taking an
  external action.
