# STATUS — pace-ai

Set 2026-10-31. Read end to end; set the date rather than appending.

## Where it is

Cloned onto Aldred's box on 2026-10-31. Last code commit 2026-07-12
(770b6a7). Nothing runs here yet: no venv, no `.env`, no database, no
unit. It has its own Remote Control session from today
(`deploy/systemd/claude-rc-pace-ai.service`), briefed below.

## The mandate, in Aldred's words (2026-10-31)

> "I think having MCP servers internally is over-engineered, and I think we
> should return to the Claude-P calls. Now that it's hosted on a box of
> mine, and simplify wherever we can and bring it into the house style.
> But before starting any work, have a look at it and see what you think."

So: review first, then simplify, then house style. The review below was
done by the coordinating session before this session existed; check it
against the code rather than trusting it.

## The review (next-pattern session, 2026-10-31)

**1. The MCP layer is already dead weight for the app.** The Flask UI
never talks to the five MCP servers. `CLAUDE.md` says so ("No MCP tool
calls from the UI"), and the code agrees: `ui/config.py` imports
`pace_ai.*` directly, `ui/context.py` and `ui/scheduling.py` import
`garmin_mcp.client`, and `sync_all` in `pace-ai/src/pace_ai/tools/sync.py`
"calls external client libraries directly". The five `server.py` files
(77 tool wrappers, roughly 2,400 lines) exist only so Claude Desktop could
be the client, which is not how it is used now. Removing them is deletion,
not a rewrite: the clients, analysis, database, prompts and workout builder
all stay. What goes with them: the `mcp` dependency, the five-package
`pip install -e` dance, the e2e "does the server boot" tests, the
integration tests of the tool wrappers, and the `_mcp` suffix on package
names. One package, one install, one test run.

**2. `claude -p` is already the fallback.** `ui/llm.py` uses OpenRouter
when `OPENROUTER_API_KEY` is set and `claude -p` otherwise. OpenRouter was
added in 732ac8a only because the cloud host had no subscription (the
commit before it reverts "mobile coaching mode (cloud API access
blocked)"). On the box the subscription applies, so drop the `openai`
dependency and the env switch. The existing fallback is not the house
shape, though: it passes `--dangerously-skip-permissions`, names no model,
and does not disable hooks, and the global Stop hook fires in headless
runs and can replace the answer. Copy the shape of
`plate-and-glass/scripts/ai` instead: an explicit cheap model per agent,
`--settings '{"disableAllHooks":true}'`, no permission bypass (the calls
need no tools at all; the data is in the prompt). STATUS makes three
parallel calls plus a readiness pass; whether that collapses to one
batched call is a judgement about latency on the phone, not a rule.

**3. House style is mostly not cosmetic.** In order of weight:

- **No auth.** `ui/app.py` binds `localhost:5050` with `debug=True`, a
  hard-coded `secret_key`, and a Flask cookie session. Nothing can be
  exposed through Caddy like this. Every other app uses the kit's
  passkeys. Two routes: front the Python app with the kit's gate (today
  the gate serves files only, so it needs a reverse-proxy mode, which is
  small Go work in the kit and belongs to the next-pattern session), or
  rewrite the app in Go on the kit. Recommendation: the gate. A rewrite
  is ten thousand lines of logic plus a Garmin library (`garth`) that only
  exists in Python. **Aldred's call; not started.**
- **Personal data lives inside the repo directory of a public repo.**
  `pace_ai.db`, `ui_sessions.db`, five `.env` files (one holding the
  Garmin password in plain text) and `~/.garth` tokens. All gitignored,
  but the house pattern is `publisher`'s: a `-workspace` directory outside
  the repo holding every personal file, one config file rather than five,
  so the repo can stay public with nothing of Aldred's in it.
- **Python, not Go.** It stays Python, for `garth` and the claims
  pipeline; it will be the odd one out and that is acceptable. It needs a
  venv (the box has Python 3.13 and no Flask), a systemd unit in the
  `nextpattern-trip` shape, and a Caddy fragment. Port and hostname from
  the map in the global brief; the DNS record is a browser step.
- **The UI is HTML in Python strings** (`ui/templates.py`, 1120 px
  desktop layout). The house is phone-first with one shared design and an
  accent per app, and everything visual original. The structure of the
  pages is fine; the shell around them is not.
- **Tests.** 649 test functions. Keep the unit tests of analysis, sync,
  database and the workout builder; drop the server-tool and e2e ones with
  the servers. `pace-ai/tests/llm_eval` (golden responses, rubrics)
  depends on OpenRouter; decide whether it is worth rewiring to `claude -p`
  or is archive.
- **The old pre-commit gauntlet in `CLAUDE.md`** (five packages, three
  test tiers each) goes with the five packages. Replace, do not keep.

**4. First boot is a real hurdle, separate from the refactor.** Four
credentials, three of them interactive: Strava OAuth with a `localhost`
callback (the box has no browser of Aldred's; the code flow needs a
paste-the-code path), Garmin SSO with MFA (`garmin-mcp-login`), Withings
OAuth, a Notion token. Plan it as its own step with Aldred on the phone,
after the app runs with no data.

**Not touched by the review:** the coaching content, the prompts, the
3,113-claim evidence base in `research/claims.db`, the analysis maths.
Those are the app. The review is about the shell around them.

## Open decisions (Aldred's)

1. Auth: gate in front of Python, or rewrite on the kit. Recommended: gate.
2. Hostname.
3. Where the workspace lives.
4. Whether `research_archive/` (2.5 MB) and the `llm_eval` suite stay.

## Next

Review the review against the code, then put the findings and a proposed
order to Aldred before changing anything. He asked to look first.
