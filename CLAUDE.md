# Pace-AI Project Rules

## Architecture

Five MCP servers + a Flask UI package in one monorepo:

### MCP Servers

1. **strava-mcp** (`localhost:8001`) — Generic Strava data access. OAuth, activities, streams, stats. 12 tools.
2. **pace-ai** (`localhost:8002`) — Running coach intelligence. Goals, analysis (ACWR/VDOT/zones), coaching prompts, methodology resources. 43 tools.
3. **garmin-mcp** (`localhost:8003`) — Garmin Connect workout management. Create, schedule, and sync structured workouts to Garmin watches. 17 tools.
4. **withings-mcp** (`localhost:8004`) — Withings body composition and health metrics. Weight, body fat, blood pressure.
5. **notion-mcp** (`localhost:8005`) — Notion running diary. Stress, niggles, and notes cached to SQLite.

Claude orchestrates between them: pulls data from strava-mcp, withings-mcp, and notion-mcp, reasons using pace-ai's coaching framework, pushes workouts via garmin-mcp.

### Flask UI (`ui/` package)

A coaching chat interface on `localhost:5050`. The `ui/` directory is a Python package split into focused modules:

| Module | Purpose |
|--------|---------|
| `ui/app.py` | Flask routes, `_render_structured_html`, `_render_plan_table_html`, `_call_claude_status`, `_merge_status_html`, `_render_group_sections` |
| `ui/config.py` | Constants, paths, system prompts, structured output section definitions (STATUS_*_SECTIONS, PLAN_REPORT_SECTIONS, NUTRITION_*_SECTIONS), `_build_structured_prompt`, `_build_plan_prompt` |
| `ui/templates.py` | HTML/CSS/JS template strings (Inter font, 1120px layout, RAG status styling) |
| `ui/context.py` | Parallel status context builders (`_build_training_context`, `_build_recovery_context`, `_build_injury_context`, `_build_readiness_context`), `_gather_status_data`, `_render_body_comp_html`, `_render_schedule_html`, plus plan/chat/nutrition contexts |
| `ui/plans.py` | `_extract_weekly_plan`, `_strip_plan_json`, `_enrich_plan_with_exercises`, `_format_plan_table`, `_default_date_range` |
| `ui/sessions.py` | Session store: `_init_session_db`, `_load_session`, `_save_session`, `_delete_session`, `_get_store`, `_persist_store` |
| `ui/scheduling.py` | Garmin workout scheduling: `_exercises_to_steps`, `_description_to_steps`, `schedule_plan_to_garmin` |

Uses a **6-agent pattern** — each coaching interaction is a focused `claude -p` subprocess call. All agent outputs (STATUS, PLAN, NUTRITION) use **structured JSON** inside ```json fences, rendered into styled section cards with RAG status indicators (green/amber/red). No emoji in any agent output.

1. **STATUS** — Split into **3 parallel** `claude -p` calls (training load, recovery, injury) run via `ThreadPoolExecutor`, followed by a sequential **readiness** pass that synthesises the results. Body composition and upcoming schedule sections are **rendered directly from data** without using Claude. Cached per session.
2. **PLAN** — Takes the status snapshot + date range and generates a structured training plan as JSON (report sections + sessions array). Rendered as section cards + a deterministic sessions table. Cites coaching research.
3. **CHAT** — Lightweight conversational agent for follow-up questions. Gets status + pending plan as context.
4. **EXERCISE** — Enriches strength/mobility sessions in a plan with structured exercise arrays (for Garmin workout sync).
5. **NUTRITION** — Sports nutrition advice in three modes: general (weekly principles), plan-paired (day-by-day for confirmed plan), race fueling (race-week strategy). Route: `/nutrition` with `mode` parameter (general, plan, race). Context built in `context.py`, queries nutrition-specific research claims. Output rendered as structured section cards.
6. **END SESSION** — Summarises the session, logs coaching notes, and updates the coaching context for next time.

**Hard boundary:** Flask owns all deterministic operations (data sync, DB writes, session management, Garmin scheduling, coaching log persistence). Claude handles only reasoning and natural language generation. No MCP tool calls from the UI — all data is gathered by Flask and injected into system prompts.

### Athlete Facts — Nutrition Category

The `athlete_facts` system supports a `nutrition` category for dietary preferences and restrictions. Examples: "omnivore", "caffeine sensitive", "prefers whole foods over supplements". The NUTRITION agent receives all facts where `category = 'nutrition'` and personalises advice accordingly.

Valid categories: `injury`, `training_response`, `goal`, `preference`, `nutrition`, `other`.

**UI tests are intentionally deferred** — the UI is in active development and the interface is changing frequently.

## Development Commands

```bash
# Install (from each subdirectory)
cd strava-mcp && pip install -e .
cd pace-ai && pip install -e .
cd garmin-mcp && pip install -e .
cd withings-mcp && pip install -e .
cd notion-mcp && pip install -e .

# Run MCP servers
strava-mcp          # starts on localhost:8001
pace-ai             # starts on localhost:8002
garmin-mcp          # starts on localhost:8003
withings-mcp        # starts on localhost:8004
notion-mcp          # starts on localhost:8005

# Run UI
python -m ui.app    # starts on localhost:5050

# Auth (garmin-mcp requires one-time login)
garmin-mcp-login    # interactive Garmin Connect SSO

# Tests (~628 test functions, more with parametrize)
cd strava-mcp && python -m pytest tests/           # all strava-mcp tests (54)
cd pace-ai && python -m pytest tests/              # all pace-ai tests (~360 functions)
cd garmin-mcp && python -m pytest tests/           # all garmin-mcp tests (~131)
cd withings-mcp && python -m pytest tests/         # all withings-mcp tests (41)
cd notion-mcp && python -m pytest tests/           # all notion-mcp tests (42)
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
cd withings-mcp && python -m pytest tests/unit/ && cd ..
cd notion-mcp && python -m pytest tests/unit/ && cd ..

# Step 2: Integration tests (all servers)
cd strava-mcp && python -m pytest tests/integration/ && cd ..
cd pace-ai && python -m pytest tests/integration/ && cd ..
cd garmin-mcp && python -m pytest tests/integration/ && cd ..
cd withings-mcp && python -m pytest tests/integration/ && cd ..
cd notion-mcp && python -m pytest tests/integration/ && cd ..

# Step 3: E2E startup tests (all servers MUST actually boot and respond to HTTP)
cd strava-mcp && python -m pytest tests/e2e/ && cd ..
cd pace-ai && python -m pytest tests/e2e/ && cd ..
cd garmin-mcp && python -m pytest tests/e2e/ && cd ..
cd withings-mcp && python -m pytest tests/e2e/ && cd ..
cd notion-mcp && python -m pytest tests/e2e/ && cd ..

# Step 4: Lint
ruff check strava-mcp/ pace-ai/ garmin-mcp/ withings-mcp/ notion-mcp/
ruff format --check strava-mcp/ pace-ai/ garmin-mcp/ withings-mcp/ notion-mcp/
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
- `respx` for mocking HTTP in strava-mcp, withings-mcp, and notion-mcp tests, mock at class level for garmin-mcp, `pytest-asyncio` for async tests
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
| **UI** | |
| `ui/app.py` | Flask routes, structured JSON renderer, parallel status orchestration (localhost:5050) |
| `ui/config.py` | Constants, paths, system prompts, structured output section definitions, `_build_structured_prompt` |
| `ui/templates.py` | HTML/CSS/JS template strings (Inter font, muted palette, RAG status indicators) |
| `ui/context.py` | Parallel status context builders, direct-render functions, plan/chat/nutrition contexts |
| `ui/plans.py` | Plan extraction, formatting, exercise enrichment |
| `ui/sessions.py` | SQLite-backed server-side session store |
| `ui/scheduling.py` | Garmin workout step builders and scheduling logic |
| **strava-mcp** | |
| `strava-mcp/src/strava_mcp/server.py` | MCP server entry point (12 tools, 2 resources) |
| `strava-mcp/src/strava_mcp/client.py` | Strava API wrapper with token refresh |
| `strava-mcp/src/strava_mcp/auth.py` | OAuth2 flow + token storage |
| `strava-mcp/tests/e2e/test_server_startup.py` | E2E: boots server, verifies HTTP response |
| **pace-ai** | |
| `pace-ai/src/pace_ai/server.py` | MCP server entry point (43 tools) |
| `pace-ai/src/pace_ai/database.py` | SQLite: goals, athlete profile, history, coaching log, sessions |
| `pace-ai/src/pace_ai/tools/analysis.py` | ACWR, VDOT, Riegel, training zones |
| `pace-ai/src/pace_ai/tools/goals.py` | Goal CRUD operations |
| `pace-ai/src/pace_ai/tools/memory.py` | Coaching context, athlete facts (incl. nutrition category), coaching log |
| `pace-ai/src/pace_ai/tools/history.py` | Activity history queries, weekly distances |
| `pace-ai/src/pace_ai/tools/profile.py` | Athlete profile management |
| `pace-ai/src/pace_ai/tools/sync.py` | Data sync orchestration (Strava, Garmin, Withings, Notion) |
| `pace-ai/src/pace_ai/prompts/coaching.py` | Coaching prompt templates |
| `pace-ai/src/pace_ai/resources/methodology.py` | Running science knowledge base |
| `pace-ai/tests/e2e/test_server_startup.py` | E2E: boots server, verifies HTTP response |
| **garmin-mcp** | |
| `garmin-mcp/src/garmin_mcp/server.py` | MCP server entry point (17 tools, 1 resource) |
| `garmin-mcp/src/garmin_mcp/client.py` | Garmin Connect API wrapper via garminconnect + garth |
| `garmin-mcp/src/garmin_mcp/auth.py` | Garth SSO auth + login_cli entry point |
| `garmin-mcp/src/garmin_mcp/workout_builder.py` | Pure functions: description → Garmin workout JSON. `SPORT_TYPE_MAP` + `resolve_sport_type()` for FR245-compatible sport types |
| `garmin-mcp/tests/e2e/test_server_startup.py` | E2E: boots server, verifies HTTP response |
| **withings-mcp** | |
| `withings-mcp/src/withings_mcp/server.py` | MCP server entry point (5 tools, 1 resource) |
| `withings-mcp/src/withings_mcp/client.py` | Withings API wrapper with token refresh |
| `withings-mcp/src/withings_mcp/auth.py` | OAuth2 flow + token storage |
| `withings-mcp/tests/e2e/test_server_startup.py` | E2E: boots server, verifies HTTP response |
| **notion-mcp** | |
| `notion-mcp/src/notion_mcp/server.py` | MCP server entry point (1 tool, 1 resource) |
| `notion-mcp/src/notion_mcp/client.py` | Notion API client + page parser |
| `notion-mcp/src/notion_mcp/cache.py` | SQLite diary entry cache |
| `notion-mcp/tests/e2e/test_server_startup.py` | E2E: boots server, verifies HTTP response |
