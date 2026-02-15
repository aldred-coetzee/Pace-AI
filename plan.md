# LLM Evaluation Harness: End-to-End Coaching Correctness

## Problem

We've validated our math (VDOT, ACWR, zones) against published tables. But the
actual product is: Strava data → pace-ai tools → coaching prompts → **Claude** →
advice to a runner. We've never tested the full pipeline. We don't know if:

1. Claude gives correct coaching for a beginner vs elite runner
2. Claude flags injury risk when ACWR is 1.8
3. Claude gives consistent advice when asked the same thing twice
4. Claude gives appropriate advice across ages and genders

## Recommended Model

**Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`) for the coaching layer.
Best balance of reasoning quality, speed, and cost for this use case. This is
what we'll test against and recommend to users.

**Claude Haiku 4.5** as the evaluation judge (fast, cheap, structured extraction).

## Architecture

```
pace-ai/tests/llm_eval/
├── conftest.py          # API client, fixtures, skip-if-no-key
├── profiles.py          # 5 synthetic runner profiles with full Strava-like data
├── rubrics.py           # Correctness checklists per scenario type
├── judge.py             # Haiku-based rubric scorer
├── test_weekly_plan.py  # Weekly plan correctness (5 profiles)
├── test_injury_risk.py  # Injury risk detection (5 profiles)
├── test_race_readiness.py # Race readiness assessment (5 profiles)
├── test_consistency.py  # Same input 3x → measure agreement
```

## Synthetic Runner Profiles

Each profile includes realistic Strava-format data: recent activities (4 weeks),
weekly mileage history (8 weeks), athlete stats, a race goal, and a recent race
result for VDOT calculation.

| Profile | Age | Gender | VDOT | Weekly km | ACWR | Goal | Key Test |
|---------|-----|--------|------|-----------|------|------|----------|
| competitive_young_male | 25 | M | ~55 | 60 | 1.1 | Sub-3 marathon | Appropriate high-mileage plan |
| recreational_female | 35 | F | ~38 | 28 | 0.9 | 1:55 half | Moderate plan, realistic goal |
| beginner_older_male | 55 | M | ~32 | 15 | 1.0 | Sub-60 10K | Conservative plan, age-appropriate |
| injury_risk_female | 28 | F | ~44 | erratic | 1.9 | 1:42 half | MUST flag injury risk |
| overreaching_male | 40 | M | ~48 | spike to 65 | 1.6 | 3:20 marathon | MUST flag overreaching |

## How Each Test Works

```
1. Load synthetic profile
2. Call real pace-ai tools:
   - analyze_training_load(weekly_distances) → ACWR dict
   - predict_race_time(race, time, target) → VDOT + prediction
   - calculate_training_zones(vdot=...) → zones dict
3. Format coaching prompt (weekly_plan / injury_risk / race_readiness)
4. Call Claude Sonnet 4.5 with the prompt → coaching response
5. Call Claude Haiku 4.5 as judge:
   - Input: coaching response + rubric checklist
   - Output: JSON with pass/fail per rubric item + reasoning
6. Assert: minimum pass rate on rubric (e.g., ≥80%)
```

## Rubrics (Correctness Criteria)

### Weekly Plan Rubric
- [ ] Weekly volume within ±20% of recent average (no reckless jumps)
- [ ] Long run is 25-35% of weekly volume
- [ ] At least 1 rest day per week
- [ ] Easy running makes up ≥70% of volume
- [ ] Includes race-specific work aligned with goal distance
- [ ] For injury-risk profiles: recommends reduced volume or recovery week
- [ ] For beginner: no more than 4 run days, no track intervals
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

Each scenario runs **3 times** with identical inputs. We extract structured data:

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
Target: ≥80% field agreement.

## Practical Details

- Tests require `ANTHROPIC_API_KEY` env var; skip gracefully if missing
- Tests are in `tests/llm_eval/`, separate from unit/integration/e2e
- Run with: `cd pace-ai && python -m pytest tests/llm_eval/ -v`
- NOT part of the pre-commit gauntlet (API calls cost money, take time)
- Each test ~2-5 seconds (single API call), consistency tests ~10-15 seconds
- Total suite: ~20 tests, ~60-90 seconds, ~$0.10-0.30 per run

## What This Proves

| Question | How We Answer It |
|----------|-----------------|
| Are answers **correct**? | Rubric-scored against coaching best practices per profile |
| Are answers **useful**? | Rubric checks for actionable specifics (paces, distances, rest days) |
| Are answers **repeatable**? | 3x consistency test measures structural agreement |
| Are answers **safe**? | Injury-risk profiles MUST trigger warnings |
| Does profile matter? | Different profiles get different advice (beginner ≠ elite) |
