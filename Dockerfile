FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY scripts ./scripts

RUN pip install --upgrade pip setuptools wheel && \
    pip install -e .

EXPOSE 8080

CMD ["sh", "-c", "if [ \"${ECP_BOOTSTRAP_DB:-false}\" = \"true\" ]; then python scripts/init_db.py; fi && if [ \"${ECP_AUTO_SEED_DEMO:-false}\" = \"true\" ]; then python scripts/seed_data.py; fi && uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
