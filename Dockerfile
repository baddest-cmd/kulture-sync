FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Stage 1: Build manifests
COPY pyproject.toml /app/kulture-sync/pyproject.toml

RUN mkdir -p /app/kulture-sync/src/kulture_sync \
    && touch /app/kulture-sync/src/kulture_sync/__init__.py \
    && pip install --no-cache-dir -e /app/kulture-sync

# Stage 2: Full source
COPY . /app/kulture-sync

WORKDIR /app/kulture-sync
EXPOSE 8080

CMD ["uvicorn", "kulture_sync.app:app", "--host", "0.0.0.0", "--port", "8080"]
