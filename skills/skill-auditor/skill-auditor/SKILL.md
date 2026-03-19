---
name: skill-auditor
description: Pre-install security gate for Claude Code skills. Automatically intercepts `npx skills add` commands, fetches the skill files from GitHub, runs an LLM-based security audit (and optionally Aguara), and shows a risk report before allowing installation. Use this skill when users want to audit, vet, review, or scan skills for security before installing. Also triggers when users say "is this skill safe", "check this skill", "scan my installed skills", or "audit skills". Can also scan already-installed skills on demand.
---

# Skill Auditor

A pre-install security gate that catches what static scanners miss — by using an LLM to reason about skill intent, not just pattern-match.

## How It Works

### Automatic Mode (Pre-Install Hook)

When configured as a hook, skill-auditor intercepts every `npx skills add` command:

1. **Intercepts** the install command before it runs
2. **Fetches** the skill files from GitHub (no git clone — just the relevant files)
3. **Scans** with Aguara if installed (optional, for static pattern matching)
4. **Audits** with Claude API — the core value-add, reasoning about intent
5. **Reports** findings with a risk level (LOW / MEDIUM / HIGH / CRITICAL)
6. **Blocks** MEDIUM+ risk installs until the user explicitly retries

On retry within 5 minutes, the cached result is used and the install proceeds — this is the "soft warn" pattern. The user always sees the report before anything installs.

### Manual Mode (On-Demand Scanning)

You can also scan skills that are already installed:

```bash
# Scan a single installed skill
/Users/shane/Documents/playground/.venv/bin/python3 ~/.claude/skills/skill-auditor/scripts/audit.py --scan-local ~/.agents/skills/nblm

# Scan ALL installed skills
/Users/shane/Documents/playground/.venv/bin/python3 ~/.claude/skills/skill-auditor/scripts/audit.py --scan-all
```

## Setup

### 1. Configure the Hook

Add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/shane/Documents/playground/.venv/bin/python3 /Users/shane/.claude/skills/skill-auditor/scripts/audit.py"
          }
        ]
      }
    ]
  }
}
```

### 2. Set Your API Key

The script reads `ANTHROPIC_API_KEY` from the environment. Make sure it's set in your shell profile or `.env`.

### 3. Optional: Install Aguara

For additional static pattern scanning:

```bash
go install github.com/garagon/aguara/cmd/aguara@latest
```

Aguara is optional — the LLM audit runs regardless.

## What It Detects (13 Categories)

### Static Analysis Overlap (second opinion alongside Aguara)
1. **Prompt injection** — hidden instructions, delimiter injection
2. **Data exfiltration** — env vars, SSH keys, credentials being read/sent
3. **Filesystem abuse** — writing to startup files, reading sensitive paths
4. **Obfuscation** — base64, unicode tricks, zero-width characters

### LLM-Unique (the real value-add)
5. **Intent & scope coherence** — does actual behavior match the stated description?
6. **Agent social engineering** — "user already approved", role-switching, urgency framing, output suppression
7. **Conditional / rug-pull logic** — triggers based on date, environment, or user input
8. **Cross-file coordination** — SKILL.md says "run setup.sh" but setup.sh does something different

### Inspired by Community Vetters
9. **Dependency risks** — typosquatted packages, unusual registries
10. **Permission combinations** — network + shell = exfiltration risk
11. **Typosquat detection** — skill name suspiciously similar to popular skills
12. **Metadata verification** — anonymous author, vague description, missing version
13. **Version delta risk** — diff against previous version if one exists locally

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | API key for Claude |
| `SKILL_AUDITOR_MODEL` | `claude-sonnet-4-6-20250514` | Model for security analysis |
| `SKILL_AUDITOR_CACHE_TTL` | `300` | Seconds before cached result expires |
| `SKILL_AUDITOR_SKIP_AGUARA` | `0` | Set to `1` to skip Aguara even if installed |

## Report Format

```
============================================================
  SKILL SECURITY AUDIT: owner/repo@skill-name
============================================================

Aguara:     2 warnings (hardcoded path, curl|bash pattern)
LLM Review: MEDIUM risk

Findings:
  [HIGH]     scripts/install.sh writes to ~/.config without disclosure
  [MEDIUM]   SKILL.md requests broad filesystem access
  [LOW]      No credential exfiltration patterns detected
  [INFO]     Author has 126 GitHub stars, account age 3 years

Overall Risk: MEDIUM
Recommendation: Review findings before installing

To proceed, run the install command again within 5 minutes.
============================================================
```
