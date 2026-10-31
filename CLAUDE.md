# Pace-AI Project Rules

## Standing brief (2026-10-31)

This app was built February to July 2026 elsewhere and moved onto Aldred's
box on 2026-10-31. It is being simplified in steps: the MCP servers are
gone and the LLM calls are `claude -p` again (both 2026-10-31); personal
data moving out of the repo and the house style come next. **`STATUS.md` holds the mandate in
Aldred's words, the review, and the open decisions; read it first.** The
global brief in `~/.claude/CLAUDE.md` names the fixed references for each
concern (passkeys and shell from the kit, systemd and persist from
`nextpattern-trip`, unattended `claude -p` from `plate-and-glass/scripts/ai`).

## Shape (2026-10-31, after the MCP servers were removed)

One package, `src/pace_ai`, plus the Flask UI in `ui/`, one `pyproject.toml`
at the root, one test tree. `README.md` has the layout table and the agent
table; do not duplicate them here.

**Hard boundary:** Flask owns every deterministic operation (sync, DB
writes, sessions, Garmin scheduling, coaching-log persistence). The model
only reasons and writes. Every model call goes through `ui/llm.py:call_llm`
with an `agent` name; the data is in the prompt and the call has no tools.
STATUS uses no model at all (`ui/status.py`, rule-based). Outputs are
structured JSON in fences rendered as section cards; no emoji in any agent
output.

Do not reintroduce MCP servers or a second LLM provider. They were removed on
purpose: the UI never used the servers, and OpenRouter existed only because a
previous host had no subscription.

### Athlete Facts — Nutrition Category

The `athlete_facts` system supports a `nutrition` category for dietary preferences and restrictions. Examples: "omnivore", "caffeine sensitive", "prefers whole foods over supplements". The NUTRITION agent receives all facts where `category = 'nutrition'` and personalises advice accordingly.

Valid categories: `injury`, `training_response`, `goal`, `preference`, `nutrition`, `other`.

**UI tests are intentionally deferred** — the UI is in active development and the interface is changing frequently.


## Commands

```bash
. .venv/bin/activate            # created with uv; `uv pip install -e ".[dev]"`
python -m ui.app                # localhost:5050
pace-ai-garmin-login            # one-time Garmin SSO (MFA)
python -m pytest -q             # whole suite, ~530 tests, ~2 s
ruff check . && ruff format --check .
```

## Before every commit

`python -m pytest -q` and both ruff commands pass for the whole repo. Docs-only
commits are exempt. Never commit credentials or any personal data. All of it lives in the
workspace (`~/.local/share/pace-ai`, or `$PACE_AI_WORKSPACE`: `config.env`,
databases, `garth/`, `withings/`), loaded by `src/pace_ai/workspace.py`; the
template is `config.example.env`. `*.db` is gitignored except
`research/claims.db`, which is curated.

## Coding conventions

- Python 3.10+, type hints, `from __future__ import annotations` in every module
- Line length 120; ruff config in the root `pyproject.toml`
- SQLite for persistence; garth for Garmin session tokens
- Tests: `respx` for HTTP in the Strava, Withings and Notion clients; Garmin
  mocked at class level; `pytest-asyncio` in auto mode. Mock external APIs,
  never our own code. Dates in tests are relative to today: hard-coded dates
  rot inside rolling windows (fixed twice already, d7c77a7 and a121d96).
- `tests/llm_eval` grades the app's real PLAN prompt (`app_prompt.py` seeds a
  throwaway DB from a synthetic profile and runs the `/status` then `/plan`
  code) through `claude -p`. It is in the normal run in offline mode (golden
  responses, no model call); `--live-llm` is opt-in and calls the model
  (`--gen-model`/`--judge-model`, aliases like `haiku`). The flags live in the
  root `conftest.py`.
- UI tests are still deferred; the UI changes next.
