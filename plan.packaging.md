# Plan: Package Pace-AI for Local Installation

**Goal:** Make both MCP servers installable, discoverable, and usable by anyone
with a Strava account and Claude Desktop/Code. Treat yourself as User #1.

---

## Phase 1: Foundation — License, Metadata, Dev Dependencies

### 1.1 Add LICENSE file
- Create `/LICENSE` with MIT license text (matches pyproject.toml declarations)

### 1.2 Enrich both pyproject.toml files
For both `strava-mcp/pyproject.toml` and `pace-ai/pyproject.toml`:
- Add `[project.urls]`: Homepage, Repository, Bug Tracker
- Add classifiers: Development Status (Alpha), Framework, Topic, License, Python versions
- Add keywords: `["mcp", "strava", "running"]` / `["mcp", "running", "coaching", "vdot"]`
- Add `[project.optional-dependencies]` for dev/test:
  ```
  dev = ["pytest>=8", "pytest-asyncio>=0.23", "respx>=0.21", "ruff>=0.4"]
  ```
  (respx only for strava-mcp)

### 1.3 Fix strava-mcp crash-on-import without env vars
- `strava-mcp/src/strava_mcp/config.py`: Change `Settings.from_env()` to not raise
  ValueError at import time. Instead, defer validation to when the server actually
  starts (in `main()` or on first API call). This lets `pip install strava-mcp` and
  `--help` work without env vars set.
- Update all tests that rely on the current behavior.

---

## Phase 2: Documentation — READMEs That Actually Help

### 2.1 Root README.md (`/README.md`)
Structure:
- **What is Pace-AI** — One paragraph. Two MCP servers, Claude orchestrates between them.
- **Architecture diagram** — Simple ASCII showing Claude ↔ strava-mcp ↔ Strava API,
  Claude ↔ pace-ai ↔ SQLite.
- **Quick Start** — Numbered steps:
  1. Create a Strava API app (link to strava.com/settings/api, explain what to set
     for callback URL)
  2. Install both servers (`pip install strava-mcp pace-ai` or `pip install -e .`
     from each dir)
  3. Configure env vars (copy `.env.example`, fill in Strava credentials)
  4. Add to Claude Desktop config (exact JSON snippet)
  5. Start a conversation: "Analyze my last week of running"
- **What You Can Do** — Grouped by server:
  - strava-mcp: list tools with one-line descriptions
  - pace-ai: list tools, prompts, resources with one-line descriptions
- **Configuration Reference** — Table of all env vars for both servers
- **Development** — How to clone, install in dev mode, run tests, lint
- **License** — MIT

### 2.2 strava-mcp README.md
- Focused on the Strava MCP server specifically
- Installation, configuration, tools reference (with example inputs/outputs),
  OAuth flow explanation, troubleshooting (common errors)

### 2.3 pace-ai README.md
- Focused on the coaching intelligence server
- Installation, configuration, tools/prompts/resources reference,
  methodology overview, example coaching conversations

---

## Phase 3: MCP Integration Config — Claude Desktop & Claude Code

### 3.1 Claude Desktop config snippet
- Document the exact `claude_desktop_config.json` entry for both servers:
  ```json
  {
    "mcpServers": {
      "strava-mcp": {
        "command": "strava-mcp",
        "env": {
          "STRAVA_CLIENT_ID": "your_id",
          "STRAVA_CLIENT_SECRET": "your_secret"
        }
      },
      "pace-ai": {
        "command": "pace-ai"
      }
    }
  }
  ```
- Note: Since both servers use `streamable-http` transport, verify this works with
  Claude Desktop's current MCP client. If Claude Desktop expects stdio transport,
  we may need to add a `--transport stdio` CLI flag or change the default.

### 3.2 Investigate transport compatibility
- **Critical question:** Claude Desktop's MCP integration — does it support
  `streamable-http` transport, or does it require `stdio`?
- If stdio is required for Claude Desktop, add a `--transport` CLI argument to both
  `main()` functions so users can choose. Default could remain `streamable-http` for
  direct HTTP usage, with docs showing `--transport stdio` for Claude Desktop.
- Claude Code (CLI) supports streamable-http natively, so no issue there.

### 3.3 Complete .env.example files
- strava-mcp: Add `STRAVA_MCP_HOST`, `STRAVA_MCP_PORT`, `STRAVA_MCP_DB` with
  comments explaining defaults
- Both: Add section headers and clearer comments

---

## Phase 4: Discoverability — GitHub & MCP Registry

### 4.1 GitHub repository polish
- Set repo description: "AI running coach powered by MCP — connects Claude to your
  Strava data for training analysis, race predictions, and coaching"
- Add topics: `mcp`, `strava`, `running`, `ai-coach`, `claude`, `training`,
  `vdot`, `model-context-protocol`
- Ensure the root README renders well (it's the storefront)

### 4.2 MCP registry manifests
- Research current MCP registry format and submission process
- Create appropriate registry config if a standard format exists
- Submit to mcp.so or equivalent registry (if one exists and accepts submissions)

---

## Phase 5: First-User Validation — Use It Yourself

### 5.1 Clean-room install test
- Fresh virtual environment
- `pip install -e ./strava-mcp -e ./pace-ai`
- Follow the README instructions exactly as written
- Configure Claude Desktop / Claude Code
- Run through a real coaching conversation
- Document any friction points

### 5.2 Fix friction points
- Whatever breaks or confuses during the clean-room test, fix it
- Update docs accordingly

---

## Phase 6: PyPI Publishing (optional, when ready)

### 6.1 Prepare for PyPI
- Verify package names `strava-mcp` and `pace-ai` are available on PyPI
- Add `long_description` pointing to README
- Build with `python -m build` in each subdirectory
- Test with `twine check dist/*`

### 6.2 Publish
- Create PyPI account (or use existing)
- `twine upload dist/*` for both packages
- Verify `pip install strava-mcp pace-ai` works from PyPI

---

## Execution Order & Dependencies

```
Phase 1 (Foundation)     — No dependencies, do first
  ↓
Phase 2 (Documentation)  — Needs Phase 1 metadata finalized
  ↓
Phase 3 (MCP Config)     — Needs transport investigation; may change Phase 2 docs
  ↓
Phase 4 (Discoverability) — Needs README done (Phase 2)
  ↓
Phase 5 (Validation)      — Needs everything above done
  ↓
Phase 6 (PyPI)            — Optional, after validation passes
```

## What I'll Implement Now (Phases 1-4)

Phases 1 through 4 are code/docs changes I can make directly. Phase 5 requires
you to actually run through the flow. Phase 6 requires PyPI credentials.

---

## Estimated Scope

| Phase | Files Changed/Created | Effort |
|-------|----------------------|--------|
| 1 | LICENSE, 2× pyproject.toml, config.py, tests | Small |
| 2 | 3× README.md | Medium |
| 3 | 2× server.py, 2× .env.example, docs | Medium |
| 4 | GitHub settings, registry config | Small |
| 5 | Manual testing, doc fixes | You |
| 6 | Build + upload | Small |
