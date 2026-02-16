# Pace-AI Plan

Two MCP servers — **strava-mcp** (Strava data access) and **pace-ai** (running
coach intelligence) — orchestrated by Claude. This plan tracks what's done, what's
next, and what's future.

---

## Completed

### Core Engineering
1. **Analysis correctness** — ACWR, VDOT, Riegel, training zones validated against published tables
2. **Validation suite** — 229 tests across both servers (strava-mcp: 54, pace-ai: 175), all passing
3. **Methodology injection** — RAG-style knowledge base separating coaching knowledge from prompt engineering
4. **Evidence base** — docs/references.md with DOI-linked citations for ACWR, 10% rule, 80/20, RED-S, youth, VDOT, taper, masters

### LLM Evaluation Harness
5. **Eval framework** — 16 synthetic runner profiles, rubric scoring, golden responses, consistency tests
6. **Judge calibration** — google/gemini-2.0-flash-001 as judge with fallback parser
7. **Model sweep** — 7 models tested across 22 profiles (16 weekly plans + 6 injury risk)
8. **Model recommendation** — Grok 4.1 Fast for standalone use (95% pass, $0.20/M); Claude via Max sub for personal use

### Packaging
9. **Foundation** — MIT LICENSE, enriched pyproject.toml files, .env.example files
10. **Documentation** — Root README.md, strava-mcp/README.md, pace-ai/README.md

### Test Counts
- **strava-mcp**: 46 unit + 7 integration + 1 e2e = 54
- **pace-ai**: 165 unit + 9 integration + 1 e2e = 175
- **llm_eval (mocked)**: 316 passed, 7 skipped (live-only)
- **Lint + format**: clean

---

## Next: Use It For Real

These are in order — each step feeds the next.

### Step 1: Connect MCP Servers to Claude
Configure strava-mcp + pace-ai as MCP servers in Claude Desktop or Claude Code.
Add the JSON config snippets, verify Claude can see both servers and list their tools.

### Step 2: Strava OAuth Setup
Complete the OAuth flow so strava-mcp can pull real activity data. Create a Strava
API application, configure callback URL, get tokens stored.

### Step 3: First Real Coaching Session
Pull Aldred's actual Strava data. Generate a return-to-running plan. This is the
end-to-end validation — the packaging plan's "Phase 3: Validate as User #1."

### Step 4: Fix Friction Points
Note every rough edge from Step 3 and fix docs/code accordingly. This is where
we find the gaps between "it works in tests" and "it works for a real person."

### Step 5: Discoverability
Once validated, get it in front of other people:
- **MCP registries** — Submit to mcp.so, smithery.ai, glama.ai
- **Awesome lists** — PR to punkpeye/awesome-mcp-servers under Sports/Fitness
- **GitHub polish** — Repo description, topics (mcp, strava, running, ai-coach, claude, vdot)
- **Community posts** — r/ClaudeAI, r/running, r/AdvancedRunning, Strava forums, X/Twitter

---

## Future: Scale Beyond Personal Use

### PyPI Publishing
- Verify `strava-mcp` and `pace-ai` names are available
- Build, check, publish — enables `pip install strava-mcp pace-ai`

### Hosted Claude Plugin (Multi-User)
Deploy as hosted service so users don't need to run anything locally:
- Per-user token/goal storage (remove single-user constraints)
- Web-based OAuth flow (replace localhost callback)
- Endpoint authentication (API keys or session tokens)
- Containerize (Docker) and deploy (Railway, Fly.io)
- Database migration: SQLite → PostgreSQL
- Strava rate limit management across users

### Standalone App
If moving beyond Claude.ai to serve users at scale:
- **LLM**: Grok 4.1 Fast as default ($0.20/M), fallback chain → DeepSeek V3.2 → Claude Sonnet 4.5
- **Infrastructure**: Hosted MCP servers, API gateway, load balancer
- **Product**: Web/mobile frontend, scheduled plan generation, training history, user onboarding
- **Safety**: Automated regression eval on prompt changes, A/B testing, user feedback loop
- **Cost**: ~$0.024/user/month on Grok at 30 requests/month

### DX Polish
- Fix strava-mcp crash-on-import when env vars missing (defer to server start)
- Add `--transport` CLI flag for stdio-based MCP clients
- Add `__version__` exports to both packages

---

## Reference

### Model Leaderboard (2026-02-15)

| Rank | Model | Cost In/M | Pass Rate | Rating | Time |
|------|-------|-----------|-----------|--------|------|
| **1** | **Grok 4.1 Fast** | **$0.20** | **95% (21/22)** | **4.5/5** | **496s** |
| 2 | Claude Sonnet 4.5 | $3.00 | 95% (21/22) | 4.7/5 | 978s |
| 3 | DeepSeek V3.2 | $0.25 | 82% (18/22) | 4.4/5 | 1862s |
| 4 | Gemini 2.5 Pro | $1.25 | 73% (16/22) | 4.4/5 | 847s |
| 5 | GPT-5 | $1.25 | 59% (13/22) | 4.2/5 | 1978s |
| 6 | GLM-4.7 | $0.40 | 59% (13/22) | 4.3/5 | 2799s |
| 7 | Kimi K2.5 | $0.45 | 59% (13/22) | 4.2/5 | 3603s |

### Model Decision: Claude via Max Sub

For personal use, Claude IS the LLM — no OpenRouter needed:
```
Claude (Max sub) → calls MCP tools → pace-ai returns coaching PROMPT → Claude generates the response
```
The model sweep validated prompts + methodology produce correct coaching (Sonnet 4.5: 95%).
Grok recommendation applies only for standalone app / multi-user at scale.

### Architecture

```
pace-ai/tests/llm_eval/
├── conftest.py            # API client, fixtures, skip-if-no-key
├── profiles.py            # 16 synthetic runner profiles
├── rubrics.py             # Correctness checklists per scenario
├── scoring.py             # Judge-based rubric scorer
├── golden_responses.py    # Reference responses for calibration
├── llm_client.py          # LLM abstraction (OpenRouter + Anthropic)
├── sweep.py               # Model comparison across profiles
├── test_weekly_plan.py    # Weekly plan correctness (16 profiles)
├── test_injury_risk.py    # Injury risk detection (6 profiles)
├── test_race_readiness.py # Race readiness assessment (16 profiles)
├── test_consistency.py    # Same input 3x → measure agreement
```

### Key Files

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
