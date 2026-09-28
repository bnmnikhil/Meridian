# Meridian Review Web Application

This folder contains only the web layer. It uses the assignment in the sibling
`fde-class2-takehome-starter` folder as its core task runner and context pack.
The core owns case evidence construction, the date and missing-information
gates, model calls, output-contract validation, and rich result construction.
The Flask application only handles HTTP input, calls the core case-task entry
point, and renders or serializes the returned result.

## Local setup

From this folder on Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
waitress-serve --host=127.0.0.1 --port=8081 web_app:app
```

Open `http://127.0.0.1:8081`. The API endpoints are `GET /api/health` and
`POST /api/run`.

The default core folder is `../fde-class2-takehome-starter`. Override it with
`MERIDIAN_CORE_DIR` when the assignment is stored elsewhere. The OpenRouter
credential remains in the assignment folder's ignored `.env` file.

## Container deployment

Use the common `Meridian` parent as the Docker build context:

```powershell
docker build -f meridian-web/Dockerfile -t meridian-review .
docker run --env-file fde-class2-takehome-starter/.env -p 8080:8080 meridian-review
```

## Ubuntu systemd deployment

The hardened unit file in `deploy/meridian-review.service` runs the application
as a dedicated `meridian` service account and binds Waitress to
`127.0.0.1:8081`. Put a TLS reverse proxy in front of it before allowing public
traffic.

The production reverse-proxy configuration is in `deploy/Caddyfile`. It serves
`meridian.bonamnikhilbabu.in` over HTTPS and forwards requests to the private
Waitress listener. DNS must contain an `A` record for `meridian` pointing to the
instance public IP before Caddy can obtain the certificate.
