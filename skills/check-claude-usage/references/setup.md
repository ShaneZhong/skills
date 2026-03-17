# First-Time Setup & Re-Authentication

When `~/.claude-browser-auth.json` doesn't exist or the session has expired, follow these steps to authenticate.

## Why This Is Needed

Claude.ai is protected by Cloudflare bot detection. Automated/headless Chrome gets blocked. The workaround is to connect agent-browser to the user's real Chrome instance where they can pass the Cloudflare challenge and log in manually.

## Steps

### Step 1: Kill all Chrome processes

All Chrome instances must be stopped first — Chrome ignores `--remote-debugging-port` if an existing instance is already running.

```bash
pkill -9 -f "Google Chrome"
```

### Step 2: Launch Chrome with remote debugging

The `--user-data-dir` flag is required to force a new Chrome instance. Without it, Chrome reuses the existing instance and ignores the debugging port flag.

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-claude 2>/dev/null &
```

Wait 3 seconds, then verify:

```bash
curl -s http://localhost:9222/json/version
```

Expected: JSON with Chrome version info. If empty, Chrome reused an existing instance — repeat from Step 1.

### Step 3: User logs in manually

Ask the user to:
1. Navigate to https://claude.ai in the Chrome window
2. Log in with their account (Google OAuth / SSO)
3. Navigate to Settings > Usage
4. Confirm they're on the usage page

### Step 4: Connect and save auth

```bash
agent-browser --cdp 9222 open https://claude.ai/settings/usage
agent-browser state save ~/.claude-browser-auth.json
```

### Step 5: Read usage and close

```bash
agent-browser snapshot
agent-browser close
```

The auth state is now saved. Future checks use the Quick Check flow from SKILL.md.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Port 9222 not responding | Chrome reused existing instance | Kill ALL Chrome processes first, use `--user-data-dir` |
| "Performing security verification" | Cloudflare blocking automated Chrome | Must use real Chrome via `--cdp`, not agent-browser's built-in Chrome |
| Auth state expired | Session cookies expired | Re-run this full setup process |
| `agent-browser` not found | Not installed | `npm i -g agent-browser && agent-browser install` |
