---
name: check-claude-usage
description: Check Claude Max subscription usage (session limits, weekly limits, extra usage). Use this skill whenever the user asks about their Claude usage, quota, remaining messages, rate limits, how much Claude they've used, whether they're close to a limit, or wants to monitor their Claude Max plan consumption. Also triggers for "check my usage", "am I running low on Claude", "how much quota do I have left", "usage stats", or any mention of Claude Max/Pro plan limits.
allowed-tools: Bash(agent-browser:*)
---

# Check Claude Max Usage

This skill uses agent-browser to read the user's Claude Max subscription usage from https://claude.ai/settings/usage. It connects to the user's real Chrome browser to bypass Cloudflare bot protection.

## Quick Check (auth state already saved)

```bash
agent-browser state load ~/.claude-browser-auth.json
agent-browser open https://claude.ai/settings/usage
agent-browser wait --load networkidle
agent-browser snapshot
agent-browser close
```

Parse the snapshot output for these key metrics:
- **Current session**: percentage used, time until reset
- **Weekly limits — All models**: percentage used, reset day/time
- **Weekly limits — Sonnet only**: percentage used, reset day/time
- **Extra usage**: amount spent, spending cap, reset date

Present the results in a clear summary table to the user.

## Handling Expired Auth

If the snapshot shows "Performing security verification" or "Verifying you are human" instead of usage data, the saved auth state has expired. Follow the First-Time Setup in [references/setup.md](references/setup.md) to re-authenticate.

Tell the user: "Your saved Claude session has expired. I need you to log in again via Chrome with remote debugging. Here's what to do..." and walk them through the setup steps.

## Important Notes

- Auth state file lives at `~/.claude-browser-auth.json` — never commit this file
- Always run `agent-browser close` when done to avoid leaked browser processes
- The usage page data includes: session usage, weekly usage (all models + Sonnet-only), and extra usage billing
- If `agent-browser` is not installed, run: `npm i -g agent-browser && agent-browser install`
