# Pace-AI

An AI running coach. A Flask web UI pulls training data from Strava, wellness
and workouts from Garmin, body composition from Withings and diary entries
from Notion into one SQLite history, reasons over it with a 3,113-claim
sports-science evidence base, and pushes structured workouts to a Garmin watch.

One Python package (`src/pace_ai`) plus the UI (`ui/`). The model is reached
through headless `claude -p` calls on a Claude subscription; nothing else
talks to a model.

## Web UI

`python -m ui.app` serves the coaching dashboard on `localhost:5050`.
Outputs are structured JSON rendered into section cards with RAG status
(green/amber/red).

| Agent | How it runs | Purpose |
|-------|-------------|---------|
| **STATUS** | Rule-based, no model (`ui/status.py`) | Training load, recent runs, recovery, injury, readiness; body composition and schedule rendered from data |
| **PLAN** | `claude -p`, Sonnet | Evidence-based training plan as structured JSON plus a sessions table |
| **CHAT** | `claude -p`, Sonnet | Follow-up questions and plan tweaks |
| **EXERCISE** | `claude -p`, Haiku | Structured exercises for strength and mobility sessions, for Garmin sync |
| **NUTRITION** | `claude -p`, Sonnet | General, plan-paired or race-fuelling advice |
| **END SESSION** | `claude -p`, Haiku | Summarise the session and update coaching memory |

Each agent's model is overridable with `PACE_AI_MODEL_<AGENT>`, e.g.
`PACE_AI_MODEL_PLAN=opus`. See `ui/llm.py` for why each flag is passed.

**Workflow:** Sync All → Status → Plan → tweak via chat → Schedule → End Session

## Layout

| Path | What |
|------|------|
| `ui/` | Flask routes, prompts (`config.py`), context builders, plans, Garmin scheduling, session store, `llm.py` |
| `src/pace_ai/tools/` | Analysis (ACWR, VDOT, zones), goals, history, memory, profile, `sync_all` |
| `src/pace_ai/database.py` | The SQLite history store |
| `src/pace_ai/resources/` | Methodology and the research claim store |
| `src/pace_ai/strava/`, `garmin/`, `withings/`, `notion/` | API clients, auth and config per source; `garmin/workout_builder.py` builds Garmin workout JSON |
| `research/` | `claims.db`, the curated evidence base |
| `tests/` | One tree, one run; `tests/llm_eval` grades the PLAN prompt (offline by default, `--live-llm` calls `claude -p`) |

## Setup

```bash
uv venv .venv && . .venv/bin/activate
uv pip install -e ".[dev]"
mkdir -p ~/.local/share/pace-ai && chmod 700 ~/.local/share/pace-ai
cp config.example.env ~/.local/share/pace-ai/config.env   # fill in the credentials
chmod 600 ~/.local/share/pace-ai/config.env
pace-ai-garmin-login      # one-time Garmin SSO, handles MFA
python -m ui.app
```

Every personal file lives in one workspace directory, never in the checkout
(the repo is public): `config.env` (all credentials), the SQLite databases
(`pace_ai.db`, `ui_sessions.db`, `strava.db`, `notion.db`), `garth/` (Garmin
session tokens) and `withings/` (Withings user tokens). The default is
`~/.local/share/pace-ai`; set `PACE_AI_WORKSPACE` to put it elsewhere. Real
environment variables override `config.env`. The Garmin email and password are
needed only for `pace-ai-garmin-login`; remove them from `config.env` after.

Strava (callback domain `localhost`), Withings and Notion (an internal
integration with read access to the diary database) each need an API app;
Garmin needs none. `config.example.env` lists every variable.

## Research Evidence

The coaching system is grounded in a database of 3,113 claims extracted from 520 peer-reviewed papers across 54 research categories. Claims are scored by population relevance and injected into coaching prompts via RAG.

Categories always queried for weekly plans:

| Category | Claims | Coverage |
|----------|--------|----------|
| strength_training_runners | 64 | Running economy, frequency, exercise selection |
| foam_rolling_mobility | 47 | ROM effects, warm-up vs recovery, protocols |
| warmup_cooldown | 72 | Static vs dynamic stretching, optimal warm-up |
| recovery_modalities | 54 | Compression, cold water, massage, foam rolling |
| concurrent_training | 59 | Strength + running interference, programming |
| overtraining_recovery | 60 | Load monitoring, monotony, session RPE |
| sleep_recovery | 60 | Sleep loss effects, performance impact |
| training_load_acwr | 70 | ACWR thresholds, injury risk, load management |
| injury_prevention_general | 57 | Gait retraining, strength for injury reduction |
| easy_recovery_running | 49 | Aerobic base, fat oxidation, mitochondrial |

Conditionally added: tendon_health, injury_lower_leg, injury_knee, injury_stress_fracture, return_to_running, detraining, marathon/half/5k training, masters_running.

## Development

```bash
python -m pytest -q       # whole suite
ruff check . && ruff format --check .
```

## License

[MIT](LICENSE)
