FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# $PORT is set by the host (e.g. Railway assigns it dynamically); 8000 is the
# local/default fallback. Migrations run on every boot - safe because Alembic
# tracks the applied revision and no-ops if there's nothing new to apply.
CMD ["sh", "-c", "alembic upgrade head && uvicorn kosma_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
