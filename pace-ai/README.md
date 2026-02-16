# pace-ai

Running coach intelligence layer — coaching prompts, methodology, goals, and training analysis via MCP. Provides the sports-science reasoning that turns raw Strava data into actionable coaching advice.

## Installation

```bash
pip install -e .

# With dev dependencies
pip install -e .[dev]
```

## Configuration

All settings are optional with sensible defaults. Copy `.env.example` if you want to customize:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `PACE_AI_HOST` | `127.0.0.1` | Server bind address |
| `PACE_AI_PORT` | `8002` | Server HTTP port |
| `PACE_AI_DB` | `pace_ai.db` | SQLite path for goals |

## Running

```bash
pace-ai
# Server starts on http://127.0.0.1:8002
```

## Tools

### Analysis

#### `analyze_training_load`

Computes ACWR (Acute:Chronic Workload Ratio) using the uncoupled method (Windt & Gabbett 2019). Returns risk classification: `optimal` (0.8-1.3), `elevated` (1.3-1.5), or `high` (>1.5).

| Parameter | Type | Description |
|-----------|------|-------------|
| `weekly_distances` | list[float] | Weekly distances in km (most recent last), minimum 5 weeks |

```json
→ {"weekly_distances": [30, 32, 35, 33, 45]}
← {"acwr": 1.35, "risk_level": "elevated", "interpretation": "Training load spike detected..."}
```

#### `predict_race_time`

Predicts race times using the Daniels/Gilbert VDOT model with Riegel formula comparison. Returns VDOT, predicted time, and equivalent performances at all standard distances.

| Parameter | Type | Description |
|-----------|------|-------------|
| `recent_race_distance` | str | e.g. "5k", "10k", "half marathon", "marathon" |
| `recent_race_time` | str | Finish time (H:MM:SS or M:SS) |
| `target_distance` | str | Distance to predict |

```json
→ {"recent_race_distance": "5k", "recent_race_time": "22:00", "target_distance": "half marathon"}
← {"vdot": 41.7, "predicted_time": "1:42:21", "equivalent_performances": {...}}
```

#### `calculate_training_zones`

Computes Daniels' five training zones (Easy, Marathon, Threshold, Interval, Repetition) from VDOT, threshold pace, and/or threshold HR.

| Parameter | Type | Description |
|-----------|------|-------------|
| `vdot` | float | VDOT value (most accurate method) |
| `threshold_pace_per_km` | str | Threshold pace as M:SS per km |
| `threshold_hr` | int | Threshold heart rate in bpm |

Provide at least one parameter. VDOT-based zones use the Daniels/Gilbert %VO2max curve for highest accuracy.

### Goals

CRUD operations for race goals, stored in SQLite.

| Tool | Parameters | Description |
|------|-----------|-------------|
| `set_goal` | `race_type`, `target_time`, `race_date?`, `notes?` | Create a goal |
| `get_goals` | *(none)* | List all goals |
| `update_goal` | `goal_id`, `race_type?`, `target_time?`, `race_date?`, `notes?` | Update a goal |
| `delete_goal` | `goal_id` | Delete a goal |

## Prompts

Prompts inject the coaching methodology as RAG-style reference material, so the LLM has evidence-based guidelines regardless of which model generates the response.

### `weekly_plan`

Generates a structured weekly training plan. Takes goals, recent activities, athlete stats, and training zones as JSON inputs.

### `run_analysis`

Post-run coaching analysis for a specific activity. Takes activity detail, streams, and goals.

### `race_readiness`

Assesses readiness for an upcoming race. Takes goals, recent activities, stats, and ACWR data.

### `injury_risk`

Injury risk assessment from training load patterns. Takes weekly distances, ACWR analysis, and recent activities.

## Resources

| URI | Description |
|-----|-------------|
| `coaching://methodology` | Complete coaching methodology — ACWR thresholds, population guidelines, periodization, evidence citations |
| `coaching://zones-explained` | Detailed explanation of each training zone with purpose and session formats |

## Methodology

The coaching knowledge base (`resources/methodology.py`) contains:

- **ACWR action thresholds** — what to recommend at each risk level
- **Population-specific guidelines** — beginners, injury-return, seniors, youth (including RED-S awareness)
- **80/20 polarized training** — easy/hard distribution
- **10% rule** — weekly volume progression limits
- **Taper protocols** — race preparation guidelines
- **Evidence citations** — DOIs for ACWR, VDOT, periodization, RED-S, masters training

When research changes, update `methodology.py` (data) — not the prompts (logic).

## Tests

```bash
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/   # Integration tests
python -m pytest tests/e2e/           # E2E server startup test

# LLM eval (requires OPENROUTER_API_KEY)
python -m pytest tests/llm_eval/ -v --live-llm
```

The LLM eval harness tests 22 synthetic runner profiles against coaching rubrics, scoring correctness, safety, and consistency. See `plan.md` for details.

## License

[MIT](../LICENSE)
