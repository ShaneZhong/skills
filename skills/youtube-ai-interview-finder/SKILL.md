---
name: youtube-ai-interview-finder
description: Find one fresh YouTube AI interview/podcast video matching strict editorial criteria, intended as the source for a blog post (substack-writer Step 1). Use when the user says "find a YouTube video for today's blog", "find an AI interview video", "auto-pick a video for substack-writer", or runs the daily content cron. Filters by duration, upload month, dedup against previously used videos, then the agent picks one with reasoning.
---

# YouTube AI Interview/Podcast Finder

Automates the source-discovery step of the `substack-writer` content pipeline. Hand-curates one YouTube video per run, matching editorial criteria for a blog post.

## When to use

- Daily cron at the start of a content pipeline that ends in Substack + Medium publishing
- Ad-hoc: "find me a video for today's blog"
- Anywhere you'd otherwise have to manually scan YouTube for a usable interview/podcast

## Editorial Criteria (hard-coded)

A candidate passes ONLY if all are true:

1. **Human-to-human conversation** — interview or podcast format. NOT a promotional/explainer/review video. NOT "AI doing the interview" (e.g. "I let AI interview me for a job").
2. **Duration** — between 10 minutes and 3 hours.
3. **Upload date** — current month (e.g. April 2026 if running in April 2026).
4. **Topic relevance** — about AI as substantive content. Reject:
    - Generic "what is AI / what is LLM" explainers
    - AI safety doom without actionable content
    - AI hiring/interview-tool reviews
    - Job-prep mock interviews
5. **Editorial value** — prefer videos with **actionable** content: someone explaining HOW they use AI for X, concrete playbooks, real workflows, real tradeoffs. Practitioner-led > pundit-led.
6. **Not previously used** — must not appear in `used_videos.json`.

## Dedup discipline (important)

A video is added to `used_videos.json` ONLY after the **full downstream pipeline (blog written + Substack published)** completes successfully. Picking a video as the day's candidate does NOT mark it used. This means a runner-up from yesterday is still eligible today.

## Workflow

### Step 1 — Run the search

When this skill loads, the system tells you the **base directory** (e.g. `Base directory for this skill: /Users/shane/.claude/skills/youtube-ai-interview-finder`). Use that to construct the script path. The env vars `$CLAUDE_PLUGIN_ROOT` and `$CLAUDE_SKILL_DIR` are **not reliably set** for locally-installed skills — always derive from the base directory.

```bash
/Users/shane/Documents/playground/.venv/bin/python \
  <base_directory>/scripts/find_video.py
```

For example, when locally installed:
```bash
/Users/shane/Documents/playground/.venv/bin/python \
  /Users/shane/.claude/skills/youtube-ai-interview-finder/scripts/find_video.py
```

This:
1. Reads `APIFY_TOKEN` from `/Users/shane/Documents/playground/.env`
2. Runs Apify actor `streamers/youtube-scraper` with 3 search queries: `"AI interview"`, `"AI podcast"`, `"interview AI founder"`
3. Filters by duration (10min–3hr), drops any video already in `used_videos.json`
4. Writes:
    - `ai_writing/auto_youtube_finder/candidates_raw_{YYYY-MM-DD}.json` — full Apify dump
    - `ai_writing/auto_youtube_finder/candidates_{YYYY-MM-DD}.json` — deduped + duration-filtered shortlist

Apify's `uploadDate=month` filter is loose — it returns videos older than a month too. The agent must filter strictly to the current month in Step 2.

### Step 2 — Agent picks one

Read `candidates_{YYYY-MM-DD}.json`. Apply the editorial criteria above. For each candidate, evaluate the **title + description + channel** to judge:
- Is this actionable practitioner content, or doom/explainer pundit content?
- Is the upload date in the current month? (Apify's filter is unreliable — re-check `date` field strictly.)
- Does the content match Shane's substack audience (solo dev / AI tools / data / business builder)?

Pick **one** winner. Pick **one** runner-up (in case the winner fails downstream). Write a JSON file with explicit reasoning:

```json
{
  "date": "YYYY-MM-DD",
  "pick": {
    "id": "...",
    "title": "...",
    "url": "...",
    "channel": "...",
    "guest": "...",
    "duration": "HH:MM:SS",
    "viewCount": 0,
    "date": "YYYY-MM-DD"
  },
  "reasoning": "Why this video — must be specific, citing the channel's reputation, the guest's track record, and the actionable value. No filler.",
  "criteria_check": {
    "human_to_human": true,
    "is_interview_or_podcast": true,
    "duration_over_10min": true,
    "this_month": true,
    "actionable_advice": true,
    "not_generic_ai_explainer": true,
    "not_used_before": true
  },
  "runner_up": { "id": "...", "title": "...", "why_runner_up": "..." },
  "rejected_with_reasons": { "<video_id>": "<one-line reason>", ... },
  "stats": { "raw_apify_results": 0, "this_month_only": 0, "passing_all_criteria": 0 }
}
```

Save as `ai_writing/auto_youtube_finder/pick_{YYYY-MM-DD}.json`.

### Step 3 — Hand off (optional)

If invoked as part of the daily content cron, emit the picked video URL to stdout / Discord, then trigger `substack-writer` with that URL as input.

After `substack-writer` finishes successfully (Substack post published), append the video ID to `used_videos.json`:

```json
{ "video_ids": ["wc8FBhQtdsA", "..."], "_doc": "..." }
```

If `substack-writer` fails, do NOT append — the video is still eligible tomorrow.

## File locations

| Path | Purpose |
|------|---------|
| `<skill_base_dir>/scripts/find_video.py` | Apify caller (skill_base_dir given on skill load) |
| `~/Documents/playground/.env` (APIFY_TOKEN) | Auth |
| `~/Documents/playground/ai_writing/auto_youtube_finder/used_videos.json` | Dedup ledger (append after publish) |
| `~/Documents/playground/ai_writing/auto_youtube_finder/candidates_raw_{date}.json` | Raw Apify dump |
| `~/Documents/playground/ai_writing/auto_youtube_finder/candidates_{date}.json` | Deduped shortlist |
| `~/Documents/playground/ai_writing/auto_youtube_finder/pick_{date}.json` | Picked video + reasoning |

## Dependencies

- Python 3.11 venv at `/Users/shane/Documents/playground/.venv`
- `apify-client`, `python-dotenv`
- `APIFY_TOKEN` in `.env`

Install if missing:

```bash
/Users/shane/Documents/playground/.venv/bin/pip install apify-client python-dotenv
```

## Common rejection patterns (for agent reference)

| Title pattern | Reason to reject |
|---------------|------------------|
| "I Let AI Interview Me for X" | AI is the interviewer, not the topic |
| "AI Job Interview Questions & Answers" | Job-prep niche, not editorial content |
| "Godfather of AI Warns / Doom / We've Lost" | Doom without actionable value |
| "Why AI CEOs Are Building Bunkers" | Pundit doom, not practitioner |
| "What is AI / Beginner's Guide to LLMs" | Generic explainer |
| Channel: news outlet (CBS / BBC / Bloomberg short clips < 20 min) | Not enough depth for blog |

## Common acceptance patterns

| Pattern | Why |
|---------|-----|
| Lenny's Podcast / Dwarkesh Patel / a16z / Latent Space | Practitioner-focused, deep |
| Guest is a builder/founder talking about HOW they build | Actionable |
| 60-120 min long-form interview | Enough material for a blog |
| Title hints at concrete claim (numbers, playbook, specific company) | Substantive |
