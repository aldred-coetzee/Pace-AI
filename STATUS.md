# STATUS — pace-ai

Set 2026-11-06. Read end to end; set the date rather than appending.

## Where it is

**The service is stopped and disabled, since 2026-11-06, on Aldred's word.**
His words, in the next-pattern session: "I don't know what service is running
on Pace AI. Perhaps we should stop it." and then "stop pace-ai". It had no
login and no address, so nothing could use it. Nothing listens on 8086; the
port stays reserved. The unit file, the venv and the workspace are untouched.
`sudo systemctl enable --now pace-ai` brings it back, and only on his word,
once auth and a hostname are decided. `claude-rc-pace-ai`, the session, stays
enabled. Checked from here: `is-enabled` says disabled, `is-active` inactive.

**Decided 2026-11-06: one user, for now.** Aldred: "Let's keep this private to
me fior now" [sic]. This session reads that as his app alone, which is an
exception to the house rule that Emmanuelle has every app. It answers a
dictated remark before it ("I am not running or an equation. So consider this
more an equation or an approach for a general running up."), read then as a
possible general running app for any runner. That is not being built: no
multi-user data model and no design note for one. "For now" leaves it open
later, and the costs if it returns are: a user on every piece of data and
source connection, a built-in diary instead of Notion, Garmin through its
official developer programme since nobody else's password can be asked for,
Strava's athlete limit, and the subscription terms on serving others (those
last three from memory, not checked at source).

**Not settled by that sentence:** the GitHub repo is still PUBLIC. It holds no
personal data, by design. Whether "private" also covers the code has been put
to him; flipping it is his, in the browser (Settings → General).

Below, as of 2026-10-31, evening. **Steps 1 and 2 of the proposed order are done**
(Aldred's go, the same evening), pushed:

- **Step 1**: `ui/llm.py` calls `claude -p` directly. Each agent names its
  model (Sonnet for chat, plan and nutrition; Haiku for end-session and
  exercise), overridable by `PACE_AI_MODEL_<AGENT>`. No tools, no permission
  bypass, hooks off, no session persistence. `openai` and OpenRouter are gone
  from the app. Verified with a real call and a bad-model call.
  **Found on the way, worth knowing in every app:** a headless call from a
  directory under `~` loads the global `~/.claude/CLAUDE.md`. Measured:
  22,035 input tokens for "say ok", against 557 with `--setting-sources
  project` run from an empty temp directory. `plate-and-glass/scripts/ai`, the
  house reference, does not pass the flag, so it pays that on every call.
  Reported to Aldred for the next-pattern session; not changed from here.
- **Step 2**: one package. The source clients live under `src/pace_ai/strava`,
  `garmin`, `withings` and `notion`; the five `server.py`, the MCP prompt
  templates, the server and e2e tests, the `mcp` dependency and the
  `sys.path` hacks are gone. One `pyproject.toml`, one test run: 532 pass,
  and ruff is clean across the whole repo (including `ui/`, which had never
  been linted). The CLI is `pace-ai-garmin-login`. The `strava_mcp.db` /
  `notion_mcp.db` filenames and `*_MCP_DB` variables were kept deliberately,
  because they name data files and renaming them would orphan data; step 3
  replaces them anyway.
- **`llm_eval` rewired** (Aldred: "rewire", decision 4 half-taken): live mode
  (`--live-llm`) now grades the app's REAL PLAN prompt, not the deleted MCP
  templates. `tests/llm_eval/app_prompt.py` seeds a temp `HistoryDB` from each
  of the 16 synthetic profiles and runs the `/status` → `/plan` code path
  (mirrored by hand, so it can drift from `ui/app.py`; extracting a shared
  function would remove that). Generation model is `model_for("plan")`,
  judge is Haiku, both through `claude -p`. The injury-risk and
  race-readiness evals were deleted: the app has no LLM agent for either
  since STATUS became rule-based. The default (golden) mode makes no model
  call and is back in the normal run: 589 pass, 5 live-only skips. One
  live profile verified with Haiku for both roles.
- **Three app bugs found by the eval, all fixed**:
  `claim_store.py` lost the path to `research/claims.db` in the step 2 move
  (`parents[4]` was right for the old layout), so `/plan` ran with NO
  research claims, silently, because the context builder swallows the
  error; neither the move nor its review caught it, which is the case for
  the eval existing. `assess_training_load` took the OLDEST week as current
  (the DB returns oldest-first), so an overreaching runner at ACWR 1.6 read
  "OK"; this predates the box. `assess_recent_runs` called `int()` on an
  "m:ss" pace string, so `/status` crashed on any synced run. Regression
  tests in `tests/ui/test_status.py`.
- **Known, not fixed, worth Aldred's eye**: weeks with no runs have no row
  (`GROUP BY week`), so a missed week drops out of the chronic average
  instead of counting as zero, and the "(current)" label goes on the latest
  week with runs, which may not be this week. And the PLAN prompt's status
  snapshot is four verdict lines: the model never sees the weekly mileage or
  the ACWR number, so it plans from "Training Load: concern" rather than the
  figures. Both are coaching quality, not plumbing.

**History rewritten locally 2026-10-31** (Aldred: "yes remove"): every
`Co-Authored-By: Claude …` trailer (97) and `claude.ai/code/session_…` link
(27) was stripped from `main`'s commit messages, under the global rule of no
AI references in commits. Trees are byte-identical and every hash changed;
hashes cited in these docs were remapped. Prose that names Claude as the
app's model was left alone, because it describes the product, not who wrote
the commit. GitHub's `refs/pull/1-5` still point at the old commits, and
nobody can rewrite those. Local backup ref: `pre-scrub-backup`. **The force-push was refused by the session's permission check; Aldred ran
it from Termux at 22:19** (`7a8b82b...5052cb2`). Any clone from before that
must be re-cloned, not pulled.

A `.venv` exists (uv, Python 3.13). There's still no real data. The old empty
package directories are gone (Aldred, 22:19).

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
added in c63b786 only because the cloud host had no subscription (the
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

## Check of the review against the code (pace-ai session, 2026-10-31)

Mostly right. Four corrections, each found by grep, not inference:

- **STATUS makes no LLM call at all.** The review and `CLAUDE.md` say three
  parallel `claude -p` calls plus a readiness pass; that was replaced
  before July. `/status` in `ui/app.py` runs the rule-based
  `assess_training_load/recent_runs/recovery/injury/readiness` in
  `ui/status.py`, no executor, no model. So the "batch STATUS into one
  call" question is moot. The LLM call sites are five: chat, plan,
  end-session, nutrition (`ui/app.py`) and exercise enrichment
  (`ui/plans.py`), all through `ui/llm.py:call_llm`.
- **Deleting the servers is not pure deletion.** `ui/scheduling.py:71`
  imports `_build_workout` from `garmin_mcp.server`. It is an eight-line
  dispatcher over `_BUILDERS`; it moves into `workout_builder.py` first.
- **`pace_ai/prompts/coaching.py` dies with the servers.** Only
  `pace_ai/server.py` imports it; the UI's prompts live in `ui/config.py`.
  The review listed "prompts" among what stays. The claim store
  (`pace_ai.resources.claim_store`) does stay; the UI queries it.
- **No personal data is on the box yet.** No `.env`, no `pace_ai.db`, no
  `ui_sessions.db`, no `~/.garth`; only `research/claims.db`, which is
  curated and tracked. The workspace can be built before first boot, so
  nothing needs moving. Note the Garmin config *requires*
  `GARMIN_PASSWORD` even when garth tokens exist; worth relaxing so the
  password is needed only at login.

Confirmed as stated: no MCP-package import outside the five `server.py`
files (2,201 lines, not 2,400); the UI imports clients directly, and puts
`pace-ai/src` and `garmin-mcp/src` on `sys.path` by hand in
`ui/config.py`; `llm.py` passes `--dangerously-skip-permissions`, no
model, hooks live; `secret_key = "pace-ai-dev-key"`, `debug=True`; 649
test functions (pace-ai 360, garmin 131, strava 54, notion 42, withings
41, root 21); `llm_eval` uses OpenRouter.

**Proposed order** (each step leaves the app runnable; 1 and 2 done 2026-10-31):

1. `call_llm` to the `plate-and-glass/scripts/ai` shape: `claude -p`,
   explicit model, hooks off, no permission bypass; drop `openai`.
2. Move `_build_workout`, delete the five `server.py`, the server tests,
   `prompts/coaching.py`, the `mcp` dependency; collapse to one package
   with one `pyproject.toml`, no `sys.path` hacks; replace the
   `CLAUDE.md` gauntlet with one `pytest` + `ruff`.
3. Workspace: one config file and every database and token under a
   directory outside the repo, passed as one flag.
4. Venv, systemd unit (trip shape), bind `127.0.0.1:8086`, real secret,
   no debug. Runs with no data.
5. Auth (decision 1) and Caddy fragment, DNS by hand.
6. First boot of the four credentials, with Aldred on the phone.
7. Phone-first shell and accent — last, because it is the largest and
   nothing above depends on it.

## Open decisions (Aldred's)

1. Auth: gate in front of Python, or rewrite on the kit. Aldred asked "why don't
   we rewrite in go?", still unanswered by him. This session's recommendation
   for one user is the gate: `garth` keeps Garmin working on his own login and
   a rewrite buys little. The gate needs a reverse-proxy mode, which is
   next-pattern's work in the kit.
2. Hostname.
3. ~~Where the workspace lives.~~ **Decided 2026-10-31: `~/.local/share/pace-ai`,
   a plain directory, no git** (Aldred chose it over a private repo with a
   persist timer). Consequence to keep in view: nothing backs it up, so the
   coaching log, athlete facts and goals, which cannot be re-synced, die
   with the box.
4. ~~`llm_eval`~~ rewired (above). Still open: whether `research_archive/`
   (2.5 MB) stays.

## Next

**Steps 3 and 4 done, 2026-10-31 late evening**, pushed:

- **Step 3, workspace**: every personal file lives in `PACE_AI_WORKSPACE`
  (default `~/.local/share/pace-ai`, 0700): one `config.env` (template
  `config.example.env`), `pace_ai.db`, `ui_sessions.db`, `strava.db`,
  `notion.db`, `garth/`, `withings/`, `secret_key`. No config searches parent
  directories any more. Garmin's password is needed only by
  `pace-ai-garmin-login`. Tests can't touch the real workspace (the root
  `conftest.py` points it at a temp dir at import time, because `ui.config`
  builds paths during collection).
- **Step 4, service**: `pace-ai-serve` (waitress, threads 8) on
  `127.0.0.1:8086`; the session key is generated into the workspace; dev
  `python -m ui.app` is loopback with debug opt-in (`PACE_AI_DEBUG=1`).
  `deploy/systemd/pace-ai.service` follows trip's shape plus `PATH` (systemd
  has no `~/.local/bin`, and every model call runs `claude`) and
  `UMask=0077`. Booted on a spare port: `GET /` 200, loopback only.
  Aldred installed it on 2026-10-31, because the permission check refused
  `sudo systemctl enable` as persistence. It ran until he stopped it on
  2026-11-06 (top of this file). The unit is still in `/etc/systemd/system`.
  Nothing is exposed until step 5 adds Caddy.

If the app stays as it is, **step 5** (auth + Caddy + DNS) waits on decisions 1
(gate or rewrite) and 2 (hostname). Step 6, the four credentials, needs Aldred
on the phone, and Strava's OAuth callback is `localhost`, so it needs a
paste-the-code path first.
