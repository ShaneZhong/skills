---
name: project-heartbeat
description: Run a long-horizon project task that survives Claude quota limits. Each tick the agent checks Claude Max session + weekly usage, does one focused unit of work toward a user-supplied goal if under the threshold, or schedules a wake-up near the next quota reset if over. Trigger when the user wants something to run unattended for hours — e.g. "keep iterating on X until done", "run this in heartbeat mode", "/project-heartbeat <goal>". Assumes planning/scoping is already done — this skill only orchestrates the loop, it does NOT decide what to build.
allowed-tools: Bash(agent-browser:*), Bash(curl:*), Bash(date:*), Bash(test:*), Bash(jq:*), Bash(cat:*), Bash(mv:*), Bash(timeout:*), Bash(flock:*), Bash(stat:*), Bash(touch:*), Bash(rm:*), Bash(git add:*), Bash(git commit:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git rev-parse:*), Bash(git branch:*), Bash(echo:*), Bash(tee:*), ScheduleWakeup, Read, Write, Edit
---

# Project Heartbeat Loop

Quota-aware self-pacing loop for long-running work. Two invocations:

- `/project-heartbeat <flags> <goal>` — **first run.** Parses args, writes state, runs tick #1.
- `/project-heartbeat --resume` — **wake-up.** Reads state, runs next tick. ScheduleWakeup always re-fires this form, never the first-run form.

## Required flags

- `--done-when '<bash command>'` — exit 0 = goal complete, loop stops. **Must be cheap (<30s, ideally <5s) — it runs every tick.** Always wrapped in `timeout 30 bash -c '<cmd>'` by the skill. Good: `test -f .ship-marker`, `git log -1 --grep='ship: x' --oneline | grep -q .`, `curl -fsS --max-time 5 https://demo.example.com/health`. Bad: full pytest suites, full lint runs, anything network-heavy.
- `--branch <name>` — work happens on this git branch only. Loop refuses to push to `main`/`master` or merge PRs. If branch doesn't match `git rev-parse --abbrev-ref HEAD`, abort.

## Optional flags (with defaults)

- `--threshold 90` — percent. If `max(checked_limits) >= threshold`, pause-loop.
- `--heartbeat 15m` — active-work cadence. 5m is too short (cache cost dominates work), 30m+ is fine.
- `--check session,weekly` — comma-list. Limits whose values gate work. Other limits are scraped but ignored.
- `--max-hours 24` — hard wall-clock stop. Loop refuses to schedule a wake past `started_at + max_hours`.

## State + lock files

State: `/tmp/project-heartbeat-state.json`
```json
{
  "goal": "...", "done_when": "<bash>", "branch": "<name>",
  "threshold": 90, "heartbeat_s": 900, "checks": ["session","weekly"],
  "started_at": "<ISO8601>", "max_hours": 24,
  "ticks": 0, "fail_streak": 0, "lock_abort_count": 0,
  "last_band": null, "tick_started_at": null
}
```

Log: `/tmp/project-heartbeat.log` — append-only. Every notification writes here via `echo "$(date -Iseconds) $msg" | tee -a /tmp/project-heartbeat.log`. User tails this to monitor. If Discord MCP is available in the session, additionally send via Discord reply — but the file log is the authoritative notify channel and must always be written.

Lock: `/tmp/project-heartbeat.lock` — `touch` at tick start, `rm -f` at tick end. **Staleness uses mtime** (each wake is a fresh process; PIDs are meaningless). A lock older than `2 * heartbeat_s` is stale. The check→clear→touch sequence is not atomic; for a single-user wake-chain that's acceptable. If parallel ticks are a real concern, use `flock -n /tmp/project-heartbeat.lock -c '...'` to wrap the entire tick body.

## Tick logic (applies to BOTH first run and resume)

> **Critical contract**: every tick calls `ScheduleWakeup` exactly ONCE, at the end (step 5). One call per turn. If a tick errors before reaching step 5, no wake fires and the loop silently dies — accepted tradeoff vs double-scheduling. Recovery: user runs `/project-heartbeat --resume`.

### 0. Init / resume

- **First run** (`/project-heartbeat <flags> <goal>`): parse args, write fresh state file, proceed.
- **Resume** (`/project-heartbeat --resume`):
  - If `/tmp/project-heartbeat-state.json` is missing: notify "Heartbeat resume failed — state file gone (likely /tmp cleared on reboot). Loop stopped." and exit. Do NOT schedule a wake. Do NOT improvise state.
  - Else: load state, proceed.

### 0.5. Concurrency + bounds

1. **Lock**: if `/tmp/project-heartbeat.lock` exists AND mtime younger than `2 * heartbeat_s`: `lock_abort_count += 1`, persist state.
   - If `lock_abort_count >= 3`: force-clear the lock, reset `lock_abort_count = 0`, notify "Forced lock clear after 3 abort-attempts", proceed with the tick (own the lock now via `touch`).
   - Else: notify "Lock held (in-flight tick), retrying in 5min", then **call `ScheduleWakeup` with `delaySeconds=300` and `prompt='/project-heartbeat --resume'`** and exit. This short retry is what eventually drives `lock_abort_count` to 3 if the in-flight tick is genuinely hung — without it, the chain dies on the first duplicate wake.
   
   Else (lock stale or missing): `rm -f` it, `touch` a fresh one, `lock_abort_count = 0`, proceed.
2. **Max-hours stop**: if `now() - started_at > max_hours`, notify + `rm -f` lock + stop. No wake.
3. **Branch check** (`git rev-parse --abbrev-ref HEAD` must equal `state.branch`). Mismatch → notify + `rm -f` lock + stop. No wake.
4. **Done-check**: `timeout 30 bash -c "$done_when"`. Exit 0 → notify "Goal met" + `rm -f` lock + stop. No wake. Exit non-zero or timeout → continue.

### 2. Read usage

Inline scrape (do NOT delegate to `/check-claude-usage` — too much overhead per tick):
1. `curl -sf http://localhost:9222/json/version` → if 200, `agent-browser --cdp 9222 open https://claude.ai/settings/usage`
2. Else: `agent-browser state load ~/.claude-browser-auth.json` then open page
3. **One in-tick retry after 10s** if Cloudflare challenge or empty progressbar.
4. On failure: `fail_streak += 1`. If `fail_streak >= 3`, notify + `rm -f` lock + stop, no further wake. If `fail_streak < 3`: **skip steps 3 and 4** (no usage data to decide on, no work to do), set `next_wake_s = 3600`, jump straight to step 5. Don't kill the loop on transient browser hiccups.

On success: `fail_streak = 0`.

Reload the URL each time — never click the in-page "Refresh" button (ref IDs drift between snapshots).

Parse: `progressbar "Usage": NN` lines for `Current session`, `All models` (weekly), `Sonnet only` (weekly).

### 3. Decide (sets `next_wake_s`, does not schedule yet)

Let `worst = max(values for limits in state.checks)`.

- **`worst < threshold - 10`** (green): do ONE unit of work (see step 4). `next_wake_s = heartbeat_s`.
- **`threshold - 10 <= worst < threshold`** (yellow / warning band): skip work this tick to slow burn. `next_wake_s = 2 * heartbeat_s` (or 3600, whichever is smaller). Notify user once per entry-into-band (compare against previous tick's band).
- **`worst >= threshold`** (red / pause): skip work. `next_wake_s = 3600` (the ScheduleWakeup cap). Don't try to parse weekly reset times — timezones make it fragile; hourly polling is cheap.

**Note on the warning band:** if work in green ticks doesn't burn enough to push `worst` into red, the loop may oscillate in yellow indefinitely — intentional throttling. `max_hours` is the ultimate stop.

**Band-entry notify:** if `current_band != state.last_band`, notify with the transition (`green→yellow`, `yellow→red`, etc.) and update `state.last_band`. Avoids spamming the log on every same-band tick.

### 4. One unit of work

The agent decides what "one unit" means based on the goal. Calibration:
- **Build a feature**: implement one screen / one endpoint / one model — NOT the whole feature.
- **Bug hunt**: one investigate → hypothesize → fix → test cycle.
- **Polish pass**: invoke ONE of `/simplify`, a single design-review subagent, or one /humanizer run.
- **Test sweep**: run the test suite once, fix one failure, re-run.

Cap: if a unit looks like it'll touch >10 files or >500 lines, split it. Stop and resume next tick.

**No enforced timeout** on the work unit — if it hangs (e.g. waiting on a network call), the tick blocks forever and the loop dies because step 5 never fires. Agent must self-discipline. Recovery: user runs `/project-heartbeat --resume`.

**Forbidden ops are enforced by `allowed-tools`**, not by documentation: `git push`, `gh pr merge`, cron/schedule mutations, Discord/Substack/Medium publishing, and `rm -rf` are NOT in the allowed-tools list — Claude Code's permission system will reject them. The skill doc lists them only as a reminder of design intent. Operator overrides (running `/project-heartbeat` in `bypassPermissions` mode) defeat this safety — don't.

### 5. Schedule next wake + release lock (always last)

1. `ticks += 1`, `tick_started_at = null`, persist state.
2. `rm -f /tmp/project-heartbeat.lock`.
3. **`ScheduleWakeup`** exactly once with `prompt = "/project-heartbeat --resume"`, `delaySeconds = next_wake_s`, and a specific `reason` like `"tick #N — green, session 27% weekly 14%, working"`. This is the only ScheduleWakeup in the normal tick path; the lock-held abort branch in step 0.5 is the sole other place that may schedule a wake (and it exits before reaching step 5, preserving one-wake-per-tick).

Stop conditions (any) → skip step 5.3 entirely (no wake), but still do 5.1 + 5.2: max-hours hit, done-when passed, branch mismatch, `fail_streak >= 3`.

## Cost notes

- Each wake reloads the full skill + state + snapshot. Roughly 8-15k tokens overhead per tick before the actual work begins. At `heartbeat=15m` × 4h = ~16 wakes = ~150-250k tokens overhead per work-hour cluster. Acceptable for unattended runs; bad for short bursts (just iterate normally).
- Paused-mode at 1h ticks: ~5-8k tokens per wake (no work). 5h session reset = ~5 wakes ≈ 30k tokens. Cheap.
- Prompt cache does NOT survive across ScheduleWakeup-triggered turns (separate sessions). Don't rely on it.

## Stopping conditions (any)

- `done_when` exits 0
- `max_hours` exceeded
- User sends a message in the active session (interrupts wake chain)
- Branch mismatch
- 3 consecutive usage-scrape failures (`fail_streak >= 3`)
- Tick errors before step 5 → loop dies silently. User runs `/project-heartbeat --resume` to recover.

## Anti-patterns

- Don't lower threshold below 70.
- Don't run multiple heartbeats on the same repo concurrently — lock will block, but you'll waste a tick figuring it out.
- Don't use this for content-publishing workflows (Discord posts, Substack, email). Use a normal cron with explicit human approval gates.
- Don't trust agent self-report of "done" — only `done_when` exit code counts.
