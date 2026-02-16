# Plan: Make Pace-AI Available to Others

**Goal:** Make both MCP servers installable, discoverable, and usable by anyone
with a Strava account and Claude Desktop/Code. Treat yourself as User #1.

---

## NOW — Ship a usable local install

### Phase 1: Foundation

**1.1 Add LICENSE file**
- Create `/LICENSE` with MIT license text (matches pyproject.toml declarations)

**1.2 Enrich both pyproject.toml files**
For both `strava-mcp/pyproject.toml` and `pace-ai/pyproject.toml`:
- Add `[project.urls]`: Homepage, Repository, Bug Tracker
- Add classifiers: Development Status (Alpha), Topic, License, Python versions
- Add keywords: `["mcp", "strava", "running"]` / `["mcp", "running", "coaching", "vdot"]`
- Add `[project.optional-dependencies]` for dev/test:
  ```
  dev = ["pytest>=8", "pytest-asyncio>=0.23", "respx>=0.21", "ruff>=0.4"]
  ```
  (respx only for strava-mcp)

**1.3 Complete .env.example files**
- strava-mcp: Add `STRAVA_MCP_HOST`, `STRAVA_MCP_PORT`, `STRAVA_MCP_DB` with
  comments explaining defaults and what each var does
- Both: Add section headers and clearer inline comments

### Phase 2: Documentation

**2.1 Root README.md** — The storefront. This is what people see first.
- **What is Pace-AI** — One paragraph. Two MCP servers, Claude orchestrates.
- **Architecture diagram** — ASCII: Claude ↔ strava-mcp ↔ Strava API,
  Claude ↔ pace-ai ↔ SQLite
- **Quick Start** — Numbered steps:
  1. Create a Strava API app (link, explain callback URL setup)
  2. Install (`pip install -e ./strava-mcp -e ./pace-ai`)
  3. Configure env vars (copy `.env.example`, fill in credentials)
  4. Add to Claude Desktop/Code config (exact JSON snippet)
  5. Start a conversation: "Analyze my last week of running"
- **What You Can Do** — Tools, prompts, resources grouped by server
- **Configuration Reference** — Table of all env vars
- **Development** — Clone, install dev mode, run tests, lint
- **License**

**2.2 strava-mcp/README.md**
- Tools reference with example inputs/outputs
- OAuth flow explanation
- Troubleshooting common errors

**2.3 pace-ai/README.md**
- Tools, prompts, resources reference
- Methodology overview
- Example coaching conversations

### Phase 3: Validate as User #1

- Fresh venv, follow the README step by step
- Configure with Claude Desktop / Claude Code
- Run a real coaching conversation end to end
- Note every friction point, fix docs and code accordingly

### Phase 4: Discoverability — Get Found

**4.1 MCP registries** — Where people actively browse for MCP servers:
- **mcp.so** — Submit both servers to the main MCP directory
- **smithery.ai** — Submit (supports one-click install)
- **glama.ai/mcp** — Submit to third directory
- Research each registry's submission format and create required config files

**4.2 Awesome MCP Servers lists**
- PR to `punkpeye/awesome-mcp-servers` (40k+ stars) under Sports/Fitness
- PR to any other active curated lists

**4.3 GitHub repository polish**
- Repo description: "AI running coach powered by MCP — connects Claude to
  your Strava data for training analysis, race predictions, and coaching"
- Topics: `mcp`, `strava`, `running`, `ai-coach`, `claude`, `training`,
  `vdot`, `model-context-protocol`

**4.4 Community posts** — One-time, high leverage:
- r/ClaudeAI — "I built an AI running coach using MCP + Strava"
- r/running, r/AdvancedRunning — "Open-source AI coach that analyzes your Strava data"
- Strava developer forums
- X/Twitter — short demo video or GIF of a real coaching conversation

---

## FUTURE — Grow reach and capabilities

### Phase 5: PyPI Publishing
- Verify `strava-mcp` and `pace-ai` names are available on PyPI
- Add `long_description` from README
- Build (`python -m build`), check (`twine check`), publish (`twine upload`)
- Enables `pip install strava-mcp pace-ai` without cloning the repo

### Phase 6: Claude Plugin (Remote MCP Integration)
Deploy as a hosted service so users can add it to claude.ai without running
anything locally. This requires solving multi-user blockers:

- **Per-user token storage** — Remove `CHECK (id = 1)` constraint, key tokens
  by athlete/session ID
- **Per-user goals** — Add `user_id` column to goals table, filter all queries
- **User-scoped cache keys** — Prefix all cache keys with user identifier
- **Web-based OAuth flow** — Replace `webbrowser.open` + localhost callback with
  a proper redirect flow through a public URL
- **Endpoint authentication** — Auth middleware on MCP HTTP endpoints
  (API keys, session tokens, or OAuth)
- **Containerize** — Dockerfile + docker-compose for deployment
- **Deploy** — Railway, Fly.io, or similar (bind `0.0.0.0`, TLS via proxy)
- **Database migration** — PostgreSQL for concurrent multi-user writes
- **Strava rate limits** — Per-user rate tracking; consider Strava partnership
  for higher limits (100 req/15min shared across all users is tight)

### Phase 7: DX Polish (as needed)
- Fix strava-mcp crash-on-import when env vars missing (defer validation
  to server start so `strava-mcp --help` works without config)
- Add `--transport` CLI flag if other MCP clients need stdio
- Add `__version__` exports to both packages

---

## What Gets Done Now

| Phase | What | Files |
|-------|------|-------|
| 1 | Foundation | LICENSE, 2× pyproject.toml, 2× .env.example |
| 2 | Documentation | 3× README.md |
| 3 | Validation | You test it end-to-end |
| 4 | Discoverability | Registry configs, GitHub settings, community posts |

Phases 1-2 are code changes I can implement directly.
Phase 3 is your hands-on testing — validate before promoting.
Phase 4 requires research into registry formats + your GitHub/Reddit accounts.
