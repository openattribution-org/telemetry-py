# Contributing to OpenAttribution Telemetry (Python)

Thank you for your interest in contributing. This repo contains the Python SDK and reference server for the [OpenAttribution Telemetry](https://github.com/openattribution-org/telemetry) standard.

## Development setup

```bash
git clone https://github.com/openattribution-org/telemetry-py.git
cd telemetry-py

# Install SDK with dev dependencies
pip install -e ".[dev]"

# Install server dependencies too
pip install -e ".[dev,server]"
```

## Running tests

```bash
pytest                       # All SDK tests
pytest tests/test_client.py  # Specific file
pytest -v                    # Verbose output
```

Tests use `pytest-asyncio` for async client tests.

## Code style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check --fix .
ruff format .
```

Key conventions:
- **Type hints everywhere**
- **Pydantic v2 patterns** (use `model_validator`, not `root_validator`)
- **Async by default** for I/O operations
- **British English** in documentation

## Schema changes

The specification lives in [openattribution-org/telemetry](https://github.com/openattribution-org/telemetry). If your change affects the data model:

1. Open an issue or PR in the spec repo first
2. Update `schema.json` (vendored copy) to match the approved spec change
3. Update `src/openattribution/telemetry/schema.py` (Pydantic models)
4. Add or update tests

## Submitting changes

1. Fork the repository and create a branch from `main`
2. Make your changes with tests
3. Ensure `pytest` and `ruff check` pass
4. Open a pull request with a clear description of the change

## Licence

By contributing, you agree that your contributions will be licensed under the Apache 2.0 licence.
