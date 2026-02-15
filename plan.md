# LLM Evaluation Harness: End-to-End Coaching Correctness

## Problem

We've validated our math (VDOT, ACWR, zones) against published tables. But the
actual product is: Strava data → pace-ai tools → coaching prompts → **LLM** →
advice to a runner. We've never tested the full pipeline. We don't know if:

1. The LLM gives correct coaching for a beginner vs elite runner
2. The LLM flags injury risk when ACWR is 1.8
3. The LLM gives consistent advice when asked the same thing twice
4. The LLM gives appropriate advice across ages, genders, and populations (seniors, youth, injury-return)

## Recommended Model

**Claude Sonnet 4.5** (`anthropic/claude-sonnet-4.5` on OpenRouter) — 95% pass rate
across 22 eval profiles (16 weekly plans + 6 injury risk). Near-perfect on all
population types including safety-critical profiles (youth RED-S, injury return,
overreaching). Only failure was a deterministic keyword technicality (judge scored
it 100%, 5.0/5).

**Judge model**: google/gemini-2.0-flash-001 (fast, cheap, structured extraction).

### Model Sweep Results (2026-02-15)

| Tier | Model | Pass Rate | Det | Judge | Rating | Time |
|------|-------|-----------|-----|-------|--------|------|
| Premium | **Claude Sonnet 4.5** | **95% (21/22)** | 99% | 93% | **4.7/5** | 978s |
| Budget | DeepSeek V3.2 | 82% (18/22) | 99% | 89% | 4.4/5 | 1862s |
| Mid | Gemini 2.5 Pro | 73% (16/22) | 97% | 85% | 4.4/5 | 847s |
| *(Baseline)* | *Qwen3 235B* | *62% (10/16)* | *—* | *—* | *—* | *—* |

**Per-profile breakdown:**

| Profile | DeepSeek V3.2 | Gemini 2.5 Pro | Sonnet 4.5 |
|---------|:---:|:---:|:---:|
| 01 beginner M healthy | PASS | FAIL | PASS |
| 02 beginner F healthy | PASS | PASS | PASS |
| 03 beginner M injury return | FAIL | PASS | PASS |
| 04 beginner F injury return | PASS | FAIL | PASS |
| 05 intermediate M healthy | PASS | PASS | PASS |
| 06 intermediate F healthy | PASS | PASS | PASS |
| 07 intermediate M overreach | PASS | PASS | PASS |
| 08 intermediate F overreach | PASS | PASS | PASS |
| 09 advanced M healthy | FAIL | FAIL | PASS |
| 10 advanced F healthy | PASS | PASS | PASS |
| 11 advanced M injury risk | PASS | PASS | PASS |
| 12 advanced F injury risk | PASS | PASS | PASS |
| 13 senior M beginner | PASS | PASS | PASS |
| 14 senior F beginner | PASS | PASS | PASS |
| 15 teen M talent | FAIL | FAIL | PASS |
| 16 teen F talent | PASS | FAIL | PASS |
| IR: 03 injury return | PASS | PASS | PASS |
| IR: 04 injury return | FAIL | FAIL | PASS |
| IR: 07 overreach | PASS | PASS | PASS |
| IR: 08 overreach | PASS | PASS | FAIL* |
| IR: 11 injury risk | PASS | PASS | PASS |
| IR: 12 injury risk | PASS | PASS | PASS |

*\*Sonnet profile 08 IR: det fail (missing "reduce" keyword), but judge=100%, rating=5.0/5*

**Key findings:**
- Sonnet excels at safety-critical populations (youth RED-S, injury return, seniors)
- DeepSeek is best value at 82% for 1/20th the cost — viable with guardrails
- Gemini underperformed despite mid-tier pricing, especially on youth/beginner profiles
- Profile 09 (advanced M healthy) and 15 (teen M talent) are hardest — only Sonnet passes both

## Architecture

```
pace-ai/tests/llm_eval/
├── conftest.py            # API client, fixtures, skip-if-no-key, default models
├── profiles.py            # 16 synthetic runner profiles with full Strava-like data
├── rubrics.py             # Correctness checklists per scenario type (audited)
├── scoring.py             # Judge-based rubric scorer with fallback parser
├── golden_responses.py    # Reference responses for calibration
├── llm_client.py          # LLM abstraction (OpenRouter + Anthropic backends)
├── sweep.py               # Model comparison across profiles
├── test_weekly_plan.py    # Weekly plan correctness (16 profiles)
├── test_injury_risk.py    # Injury risk detection (6 profiles)
├── test_race_readiness.py # Race readiness assessment (16 profiles)
├── test_consistency.py    # Same input 3x → measure agreement (3 scenarios)
```

### Key Architecture Change: Methodology Injection (RAG pattern)

Prompts no longer hardcode coaching rules. Instead:

- `methodology.py` is the coaching knowledge base — population-specific guidelines,
  ACWR action thresholds, evidence-based principles
- Prompt templates inject METHODOLOGY as reference material and tell the model to apply it
- When research changes: update `methodology.py` (data), not prompts (logic)
- `docs/references.md` has all evidence citations with DOI links

This separates coaching knowledge (what to recommend) from prompt engineering (how
to ask). The model gets the same evidence base regardless of which LLM runs the
coaching layer.

## Synthetic Runner Profiles

16 profiles covering beginner through advanced, male and female, healthy and
at-risk populations including injury-return, overreaching, senior, and youth
runners. Each profile includes realistic Strava-format data: recent activities
(4 weeks), weekly mileage history (8 weeks), athlete stats, a race goal, and a
recent race result for VDOT calculation.

| # | Profile | Level | Gender | Key Test |
|---|---------|-------|--------|----------|
| 01 | beginner M healthy | Beginner | M | Conservative plan, max 4 run days |
| 02 | beginner F healthy | Beginner | F | Conservative plan, max 4 run days |
| 03 | beginner M injury return | Beginner | M | Reduced volume, no intensity |
| 04 | beginner F injury return | Beginner | F | Reduced volume, no intensity |
| 05 | intermediate M healthy | Intermediate | M | Balanced plan, race-specific work |
| 06 | intermediate F healthy | Intermediate | F | Balanced plan, race-specific work |
| 07 | intermediate M overreach | Intermediate | M | MUST flag overreaching, reduce load |
| 08 | intermediate F overreach | Intermediate | F | MUST flag overreaching, reduce load |
| 09 | advanced M healthy | Advanced | M | High-mileage plan, quality sessions |
| 10 | advanced F healthy | Advanced | F | High-mileage plan, quality sessions |
| 11 | advanced M injury risk | Advanced | M | MUST flag injury risk, adjust plan |
| 12 | advanced F injury risk | Advanced | F | MUST flag injury risk, adjust plan |
| 13 | senior M beginner | Senior | M | Age-appropriate, conservative ramp |
| 14 | senior F beginner | Senior | F | Age-appropriate, conservative ramp |
| 15 | teen M talent | Youth | M | Development-focused, no overtraining |
| 16 | teen F talent | Youth | F | Development-focused, RED-S awareness |

## How Each Test Works

```
1. Load synthetic profile
2. Call real pace-ai tools:
   - analyze_training_load(weekly_distances) → ACWR dict
   - predict_race_time(race, time, target) → VDOT + prediction
   - calculate_training_zones(vdot=...) → zones dict
3. Format coaching prompt with methodology injection:
   - Inject METHODOLOGY from methodology.py as reference material
   - Include athlete context, training load, and analysis results
4. Call LLM (via OpenRouter) with the prompt → coaching response
5. Call judge model (google/gemini-2.0-flash-001):
   - Input: coaching response + rubric checklist
   - Output: JSON with pass/fail per rubric item + reasoning
   - Fallback parser handles numbered list format
6. Assert: minimum pass rate on rubric (e.g., ≥80%)
```

## Rubrics (Correctness Criteria)

Rubrics have been audited and fixed for: overly broad forbidden terms ("interval"
was too broad), RED-S scope (now youth-female only), brittle required elements,
and max_run_days contradictions.

### Weekly Plan Rubric
- [ ] Weekly volume within ±20% of recent average (no reckless jumps)
- [ ] Long run is 25-35% of weekly volume
- [ ] At least 1 rest day per week
- [ ] Easy running makes up ≥70% of volume
- [ ] Includes race-specific work aligned with goal distance
- [ ] For injury-risk profiles: recommends reduced volume or recovery week
- [ ] For beginner: no more than 4 run days, no track intervals
- [ ] For senior: age-appropriate volume and recovery
- [ ] For youth: development-focused, no overtraining
- [ ] Paces reference the calculated training zones

### Injury Risk Rubric
- [ ] Risk level matches ACWR category (optimal/elevated/high)
- [ ] Identifies specific problematic weeks or patterns
- [ ] Provides concrete volume adjustment (not just "be careful")
- [ ] For ACWR >1.5: explicitly warns against racing or hard workouts
- [ ] For ACWR 0.8-1.3: confirms training is sustainable

### Race Readiness Rubric
- [ ] Gives a clear readiness assessment (ready / not ready / partially ready)
- [ ] References ACWR and training load data
- [ ] Flags unrealistic goals vs current fitness (VDOT-based)
- [ ] Recommends taper if race is <3 weeks away
- [ ] For high-ACWR profiles: warns against racing

## Consistency Test Design

3 scenarios (weekly plan, injury risk, race readiness), each run **3 times** with
identical inputs. We extract structured data:

```python
{
  "recommended_weekly_km": 55,
  "run_days_per_week": 5,
  "long_run_km": 18,
  "includes_rest_day": True,
  "risk_level": "elevated",
  "flags_injury_risk": True,
  "recommends_volume_reduction": True,
}
```

**Consistency score** = percentage of extracted fields that agree across all 3 runs.
Target: ≥70% field agreement.

## Practical Details

- Tests require `OPENROUTER_API_KEY` env var; skip gracefully if missing
- Tests are in `tests/llm_eval/`, separate from unit/integration/e2e
- Run with: `cd pace-ai && python -m pytest tests/llm_eval/ -v`
- Live tests: `cd pace-ai && python -m pytest tests/llm_eval/ -v --live-llm`
- NOT part of the pre-commit gauntlet (API calls cost money, take time)
- Each test ~2-5 seconds (single API call), consistency tests ~10-15 seconds
- Total suite: ~323 tests (~316 mocked + 7 live-only), ~$0.10-0.30 per live run

## What This Proves

| Question | How We Answer It |
|----------|-----------------|
| Are answers **correct**? | Rubric-scored against coaching best practices per profile |
| Are answers **useful**? | Rubric checks for actionable specifics (paces, distances, rest days) |
| Are answers **repeatable**? | 3x consistency test measures structural agreement |
| Are answers **safe**? | Injury-risk and at-risk population profiles MUST trigger appropriate warnings |
| Does profile matter? | Different profiles get different advice (beginner ≠ elite ≠ senior ≠ youth) |
| Which model is best? | Model sweep compares pass rates across all 16 profiles |

## Current Status (2026-02-15)

### Completed
1. **Analysis correctness** — ACWR, VDOT, Riegel, training zones all validated against published tables
2. **Validation suite** — 165+ unit tests in pace-ai, 46 in strava-mcp
3. **LLM eval harness** — 16 runner profiles, golden responses, rubric scoring
4. **OpenRouter integration** — llm_client abstraction supporting OpenRouter and Anthropic backends
5. **Model sweep tool** — sweep.py comparing models across profiles
6. **Judge calibration** — google/gemini-2.0-flash-001 as judge
7. **Race readiness tests** — 16 rubrics + golden responses
8. **Consistency tests** — 3 scenarios, 3x each, structural agreement
9. **Methodology injection refactoring** — RAG-style knowledge base injection into prompts
10. **Evidence base** — docs/references.md with citations for ACWR, 10% rule, 80/20, RED-S, youth, VDOT, taper, masters
11. **Population-specific methodology** — ACWR action thresholds, beginner/injury-return/senior/youth guidelines added to methodology.py
12. **Rubric audit and fixes** — forbidden "interval" too broad, RED-S scope, brittle required elements, max_run_days contradiction, judge parser fallback
13. **Model sweep completed** — DeepSeek V3.2 (82%), Gemini 2.5 Pro (73%), Claude Sonnet 4.5 (95%) across 22 profiles
14. **Model recommendation** — Claude Sonnet 4.5 selected as production coaching model

### All Tests Passing (Pre-Commit Gauntlet)
- **strava-mcp**: 46 unit + 7 integration + 1 e2e (54 total)
- **pace-ai**: 165 unit + 9 integration + 1 e2e (175 total)
- **llm_eval (mocked)**: 316 passed, 7 skipped (live-only)
- **Lint + format**: clean

### Live Eval Results (Qwen3 235B baseline — weekly plans)

| Profile | Run 2 (before) | Run 5 (after) |
|---------|---------------|---------------|
| 01 beginner M healthy | FAIL | **PASS** |
| 02 beginner F healthy | FAIL | FAIL |
| 03 beginner M injury return | FAIL | FAIL (78% judge) |
| 04 beginner F injury return | FAIL | **PASS** |
| 05 intermediate M healthy | PASS | **PASS** |
| 06 intermediate F healthy | PASS | FAIL (LLM variance) |
| 07 intermediate M overreach | FAIL | **PASS** |
| 08 intermediate F overreach | FAIL | **PASS** |
| 09 advanced M healthy | PASS | **PASS** |
| 10 advanced F healthy | PASS | **PASS** |
| 11 advanced M injury risk | FAIL | **PASS** |
| 12 advanced F injury risk | FAIL | **PASS** |
| 13 senior M beginner | FAIL | FAIL (80% judge) |
| 14 senior F beginner | FAIL | FAIL |
| 15 teen M talent | PASS | **PASS** |
| 16 teen F talent | FAIL | FAIL (judge 100%, det fail fixed) |

**Result: 10/16 passing (62.5%)**, up from 4/16 (25%) before methodology injection.

Remaining failures are Qwen3 model limitations (prescribes tempo for beginners,
exceeds senior day limits) — exactly what the model sweep should differentiate.

### Next Steps
1. ~~**Run model sweep**~~ — Done. Claude Sonnet 4.5 selected (95% pass rate)
2. **Run full live eval** — all test types (weekly plan + injury risk + race readiness) with Sonnet 4.5
3. **Run consistency tests live** — verify structural agreement across repeated prompts with Sonnet 4.5
4. ~~**Update plan with model recommendation**~~ — Done

### Environment Setup
```bash
cd ~/projects/Pace-AI
source pace-ai/.venv/bin/activate
# OPENROUTER_API_KEY in .env or ~/.bashrc
# Default judge: google/gemini-2.0-flash-001
# Default gen: anthropic/claude-sonnet-4.5 (recommended)
# Budget alt: deepseek/deepseek-v3.2
```

### Key Files Changed
| Path | Change |
|------|--------|
| pace-ai/src/pace_ai/prompts/coaching.py | Methodology injection, athlete context, training load params |
| pace-ai/src/pace_ai/resources/methodology.py | ACWR thresholds, population guidelines, evidence citations |
| pace-ai/docs/references.md | Full evidence base with DOI links |
| pace-ai/tests/llm_eval/scoring.py | Judge parser fallback for numbered list format |
| pace-ai/tests/llm_eval/rubrics.py | Audit fixes (forbidden elements, RED-S scope, required elements) |
| pace-ai/tests/llm_eval/sweep.py | Removed Qwen3 from sweep, updated prompt calls |
| pace-ai/tests/llm_eval/conftest.py | Fixed default gen model (dropped :free suffix) |
