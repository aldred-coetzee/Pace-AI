# Pace-AI Project Rules

## Architecture

Three MCP servers in one monorepo:

1. **strava-mcp** (`localhost:8001`) — Generic Strava data access. OAuth, activities, streams, stats.
2. **pace-ai** (`localhost:8002`) — Running coach intelligence. Goals, analysis (ACWR/VDOT/zones), coaching prompts, methodology resources.
3. **garmin-mcp** (`localhost:8003`) — Garmin Connect workout management. Create, schedule, and sync structured workouts to Garmin watches.

Claude orchestrates between them: pulls data from strava-mcp, reasons using pace-ai's coaching framework, pushes workouts via garmin-mcp.

## Development Commands

```bash
# Install (from each subdirectory)
cd strava-mcp && pip install -e .
cd pace-ai && pip install -e .
cd garmin-mcp && pip install -e .

# Run servers
strava-mcp          # starts on localhost:8001
pace-ai             # starts on localhost:8002
garmin-mcp          # starts on localhost:8003

# Auth (garmin-mcp requires one-time login)
garmin-mcp-login    # interactive Garmin Connect SSO

# Tests
cd strava-mcp && python -m pytest tests/           # all strava-mcp tests
cd pace-ai && python -m pytest tests/              # all pace-ai tests
cd garmin-mcp && python -m pytest tests/           # all garmin-mcp tests
python -m pytest tests/unit/                       # unit tests only
python -m pytest tests/integration/                # integration tests only
python -m pytest tests/e2e/                        # e2e tests (server startup)

# Lint
ruff check .
ruff format --check .
ruff check --fix .
```

## Pre-Commit Test Gauntlet (NON-NEGOTIABLE)

**Every commit MUST pass ALL of these steps. No shortcuts.**

**Exception:** Plan-only changes (edits solely to `plan.md` or other documentation
with no code changes) do not require the test gauntlet.

```bash
# Step 1: Unit tests (all servers)
cd strava-mcp && python -m pytest tests/unit/ && cd ..
cd pace-ai && python -m pytest tests/unit/ && cd ..
cd garmin-mcp && python -m pytest tests/unit/ && cd ..

# Step 2: Integration tests (all servers)
cd strava-mcp && python -m pytest tests/integration/ && cd ..
cd pace-ai && python -m pytest tests/integration/ && cd ..
cd garmin-mcp && python -m pytest tests/integration/ && cd ..

# Step 3: E2E startup tests (all servers MUST actually boot and respond to HTTP)
cd strava-mcp && python -m pytest tests/e2e/ && cd ..
cd pace-ai && python -m pytest tests/e2e/ && cd ..
cd garmin-mcp && python -m pytest tests/e2e/ && cd ..

# Step 4: Lint
ruff check strava-mcp/ pace-ai/ garmin-mcp/
ruff format --check strava-mcp/ pace-ai/ garmin-mcp/
```

**If ANY step fails, the commit MUST NOT proceed.**

### Why E2E Startup Tests Are Mandatory

Unit and integration tests import and call individual functions. They do NOT test:
- Whether `main()` actually starts the server without crashing
- Whether the server binds to the correct port
- Whether the MCP endpoint responds to HTTP

The e2e startup tests (`tests/e2e/test_server_startup.py`) boot the actual server as a subprocess and verify it responds. These are fast (<2 seconds each) and catch real deployment failures that no amount of unit testing can find.

**Every entry point must have a corresponding e2e test.**

## Commit Rules

1. **Never commit without passing the full test gauntlet above.** ALL tests must pass — unit, integration, AND e2e.
2. **Never commit credentials.** The `.env` file is gitignored. Use `.env.example` as template.
3. **Run ruff before committing**: `ruff check . && ruff format --check .`
4. **If you add a new entry point or server config change, add an e2e test that verifies it actually works.**

## Coding Conventions

- Python 3.10+, type hints everywhere
- `from __future__ import annotations` in every module
- Line length: 120 (configured in pyproject.toml)
- Imports sorted by ruff/isort
- Async/await for all I/O operations
- SQLite for local persistence (tokens, cache, goals); garth for Garmin session storage
- `respx` for mocking HTTP in strava-mcp tests, mock at class level for garmin-mcp, `pytest-asyncio` for async tests
- Test fixtures in `tests/conftest.py`, sample data factories for realistic test data

## Testing Philosophy

- **Unit tests**: Mock external HTTP (Strava API). Never mock our own code.
- **Integration tests**: Mock Strava API. Test MCP tools/prompts through real function calls.
- **E2E tests**: Mock nothing. Real servers, real HTTP, real SQLite. Must test every entry point.

### Test Coverage Requirements

Every module must have tests. Specifically:
- Every tool function → unit test + integration test
- Every prompt template → unit test checking structure + integration test through server
- Every resource → unit test
- Every `main()` / entry point → e2e startup test that boots the server and verifies HTTP response
- Every config parsing path → unit test including error cases

## Key Files

| Path | Purpose |
|------|---------|
| `strava-mcp/src/strava_mcp/server.py` | MCP server entry point (7 tools, 2 resources) |
| `strava-mcp/src/strava_mcp/client.py` | Strava API wrapper with token refresh |
| `strava-mcp/src/strava_mcp/auth.py` | OAuth2 flow + token storage |
| `strava-mcp/tests/e2e/test_server_startup.py` | E2E: boots server, verifies HTTP response |
| `pace-ai/src/pace_ai/server.py` | MCP server entry point (7 tools, 4 prompts, 2 resources) |
| `pace-ai/src/pace_ai/tools/analysis.py` | ACWR, VDOT, Riegel, training zones |
| `pace-ai/src/pace_ai/tools/goals.py` | Goal CRUD operations |
| `pace-ai/src/pace_ai/prompts/coaching.py` | Coaching prompt templates |
| `pace-ai/src/pace_ai/resources/methodology.py` | Running science knowledge base |
| `pace-ai/tests/e2e/test_server_startup.py` | E2E: boots server, verifies HTTP response |
| `garmin-mcp/src/garmin_mcp/server.py` | MCP server entry point (7 tools, 1 resource) |
| `garmin-mcp/src/garmin_mcp/client.py` | Garmin Connect API wrapper via garminconnect + garth |
| `garmin-mcp/src/garmin_mcp/auth.py` | Garth SSO auth + login_cli entry point |
| `garmin-mcp/src/garmin_mcp/workout_builder.py` | Pure functions: description → Garmin workout JSON |
| `garmin-mcp/tests/e2e/test_server_startup.py` | E2E: boots server, verifies HTTP response |
