# Pace-AI Project Rules

## Architecture

Two MCP servers in one monorepo:

1. **strava-mcp** (`localhost:8001`) — Generic Strava data access. OAuth, activities, streams, stats.
2. **pace-ai** (`localhost:8002`) — Running coach intelligence. Goals, analysis (ACWR/VDOT/zones), coaching prompts, methodology resources.

Claude orchestrates between them: pulls data from strava-mcp, reasons using pace-ai's coaching framework.

## Development Commands

```bash
# Install (from each subdirectory)
cd strava-mcp && pip install -e .
cd pace-ai && pip install -e .

# Run servers
strava-mcp          # starts on localhost:8001
pace-ai             # starts on localhost:8002

# Tests
cd strava-mcp && python -m pytest tests/           # all strava-mcp tests
cd pace-ai && python -m pytest tests/              # all pace-ai tests
python -m pytest tests/unit/                       # unit tests only
python -m pytest tests/integration/                # integration tests only
python -m pytest tests/e2e/ -m e2e                 # e2e tests (needs credentials)

# Lint
ruff check .
ruff format --check .
ruff check --fix .
```

## Commit Rules

1. **Never commit without running tests.** All unit + integration tests must pass.
2. **Never commit credentials.** The `.env` file is gitignored. Use `.env.example` as template.
3. **Run ruff before committing**: `ruff check . && ruff format --check .`

## Coding Conventions

- Python 3.10+, type hints everywhere
- `from __future__ import annotations` in every module
- Line length: 120 (configured in pyproject.toml)
- Imports sorted by ruff/isort
- Async/await for all I/O operations
- SQLite for local persistence (tokens, cache, goals)
- `respx` for mocking HTTP in tests, `pytest-asyncio` for async tests
- Test fixtures in `tests/conftest.py`, sample data factories for realistic test data

## Testing Philosophy

- **Unit tests**: Mock external HTTP (Strava API). Never mock our own code.
- **Integration tests**: Mock Strava API. Test MCP tools/prompts through real function calls.
- **E2E tests**: Mock nothing. Real Strava, real MCP, real SQLite.

## Key Files

| Path | Purpose |
|------|---------|
| `strava-mcp/src/strava_mcp/server.py` | MCP server entry point (7 tools, 2 resources) |
| `strava-mcp/src/strava_mcp/client.py` | Strava API wrapper with token refresh |
| `strava-mcp/src/strava_mcp/auth.py` | OAuth2 flow + token storage |
| `pace-ai/src/pace_ai/server.py` | MCP server entry point (7 tools, 4 prompts, 2 resources) |
| `pace-ai/src/pace_ai/tools/analysis.py` | ACWR, VDOT, Riegel, training zones |
| `pace-ai/src/pace_ai/tools/goals.py` | Goal CRUD operations |
| `pace-ai/src/pace_ai/prompts/coaching.py` | Coaching prompt templates |
| `pace-ai/src/pace_ai/resources/methodology.py` | Running science knowledge base |
