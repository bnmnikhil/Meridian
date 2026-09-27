FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WEB_HOST=0.0.0.0 \
    WEB_PORT=8080

WORKDIR /app/web

COPY meridian-web/requirements.txt /tmp/web-requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/web-requirements.txt

COPY fde-class2-takehome-starter /app/core
COPY meridian-web /app/web

ENV MERIDIAN_CORE_DIR=/app/core

EXPOSE 8080

CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "web_app:app"]
