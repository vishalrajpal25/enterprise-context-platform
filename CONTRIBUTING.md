# Contributing

Thank you for helping improve the Enterprise Context Platform.

## Development setup

1. Python 3.11+
2. Docker (Neo4j, PostgreSQL/pgvector, Redis)
3. Optional: Node.js 20+ for the MCP server in `src/protocol/`

```bash
docker compose up -d
python scripts/init_db.py
python scripts/seed_data.py
uvicorn src.main:app --reload --port 8080
```

## Tests

With **pip** (Python 3.11+):

```bash
python -m pip install -e ".[dev]"
PYTHONPATH=. pytest tests/ -q
```

With **uv** (matches many local setups):

```bash
uv pip install --python .venv/bin/python pytest pytest-asyncio
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q
```

Tests replace the app **lifespan** with a stub so PostgreSQL/Neo4j are not required for the default API tests.

### MCP server

```bash
cd src/protocol && npm install && npm start
```

## Pull requests

- Keep changes focused on one concern.
- Run `ruff check src tests` before submitting.
- Add or update tests for behavior changes.

## License

By contributing, you agree that your contributions are licensed under the Apache License 2.0.
