# CLAUDE.md

OpenAttribution Telemetry Python SDK and FastAPI reference server. Monorepo.

## Structure

- `src/openattribution/telemetry/` - Python SDK (httpx client, pydantic models, event schema)
- `server/` - FastAPI reference server (PostgreSQL, psycopg3, pydantic-settings)
- `tests/` - SDK tests
- `server/tests/` - Server tests
- `server/migrations/` - SQL migrations (applied manually via `make migrate`)
- `schema.json` - Canonical JSON Schema for telemetry events

## Tech stack

Python 3.11+. httpx for async HTTP. pydantic v2 for models. hatchling for build. FastAPI + uvicorn for the server. PostgreSQL via psycopg3 for storage. ruff for linting and formatting.

## Commands

```
make test          # Run all tests (SDK + server)
make test-sdk      # SDK tests only
make test-server   # Server tests only
make lint          # Lint both packages with ruff
make fmt           # Format + auto-fix both packages
make ci            # Lint + test (CI pipeline)
make dev-server    # Run server with auto-reload on :8007
make migrate       # Apply SQL migrations to $DATABASE_URL
```

## Conventions

- British English in prose and comments
- ruff line-length 100, target Python 3.11
- Async-first (pytest-asyncio with `asyncio_mode = "auto"`)
- pydantic v2 models throughout
- SDK is `openattribution-telemetry` on PyPI, imported as `openattribution.telemetry`
- Server is a separate package under `server/` with its own `pyproject.toml`
- Integration-first testing - prefer fakes over mocks, assert observable behaviour
