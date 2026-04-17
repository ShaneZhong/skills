---
name: counsel
description: "Multi-agent AI board meeting. 12 advisors debate your decision from different philosophical frameworks. Interactive HTML UI with real-time roundtable visualization. Use when facing high-uncertainty decisions."
---

# Counsel — AI Board Meeting

Multi-agent decision support system inspired by [jiangjiax/counsel](https://github.com/jiangjiax/counsel). 12 advisors examine your decision from fundamentally different angles using Nominal Group Technique (parallel, invisible generation), structured debate, and synthesis. Results displayed in an interactive browser UI in real-time.

## Advisors

Single source of truth: `~/.claude/skills/counsel/advisors.json` (served at `GET /api/advisors`). The list includes Steve Jobs, Paul Graham, Jeff Bezos, Elon Musk, Warren Buffett, Ray Dalio, Charlie Munger, Kevin Kelly, Marc Andreessen, Naval Ravikant, Peter Thiel, Albert Einstein. Read `advisors.json` when spawning agents to get exact persona framings — don't duplicate the list inline.

## Architecture

```
~/.claude/skills/counsel/
├── SKILL.md              (this file — instructions)
├── advisors.json         (SSOT for advisor personas)
├── server.py             (HTTP server + SSE)
└── templates/
    └── index.html        (interactive SPA frontend)
```

Session state (written by server, read/displayed by UI):
```
counsel-sessions/[date]-[slug]/
├── session.json          (progressive session state)
├── server.pid            (server process PID)
└── server.url            (http://localhost:<port>)
```

## Workflow

### Step 0: Launch Server + Open UI

1. Create session directory: `counsel-sessions/YYYY-MM-DD-[slug]/`
2. Start the server in the background (the server auto-probes a free port starting at 8787):
   ```bash
   SESSION_DIR="counsel-sessions/YYYY-MM-DD-[slug]"
   /Users/shane/Documents/playground/.venv/bin/python3 ~/.claude/skills/counsel/server.py --session "$SESSION_DIR" > "$SESSION_DIR/server.log" 2>&1 &
   ```
3. Wait briefly and read the URL the server picked:
   ```bash
   for i in 1 2 3 4 5; do [ -f "$SESSION_DIR/server.url" ] && break; sleep 0.5; done
   URL=$(cat "$SESSION_DIR/server.url")
   open "$URL"
   ```
4. All subsequent `curl` calls should target `$URL` (not a hard-coded `localhost:8787`). Export it once and reuse:
   ```bash
   export COUNSEL_URL="$URL"
   ```

### Chat Sync

**Every message in the terminal conversation must be synced to the UI's chat panel.** After each facilitator message or user response, POST via `curl -sf` (the `-f` makes curl fail on HTTP errors so you notice):
```bash
curl -sf -X POST "$COUNSEL_URL/api/update" -H 'Content-Type: application/json' \
  -d '{"type":"chat","data":{"role":"facilitator","text":"YOUR MESSAGE"}}'
```
Roles: `facilitator` (you), `user` (their reply), `system` (stage transitions like "Moving to advisor statements...").

### Step 1: Problem Clarification (Facilitator)

You are the **Facilitator**. Your role is process-only — never inject content opinions.

1. Read the user's raw input (confusion, question, decision they're facing)
2. Ask 2-3 clarifying questions (one at a time) to sharpen the decision into a testable question. Sync each Q via `chat` event.
3. Once clear, summarize: "The decision we're examining: **[one sentence]**" — POST an `init` event:
   ```bash
   curl -sf -X POST "$COUNSEL_URL/api/update" -H 'Content-Type: application/json' \
     -d '{"type":"init","question":"THE DECISION QUESTION","timestamp":"YYYY-MM-DD"}'
   ```
4. Spawn **12 Agent() calls in parallel** (model: sonnet), each asking ONE critical question the advisor would need answered. Advisor personas come from `advisors.json` — read it at startup.
5. As each agent returns, POST an `advisor_question` event:
   ```bash
   curl -sf -X POST "$COUNSEL_URL/api/update" -H 'Content-Type: application/json' \
     -d '{"type":"advisor_question","data":{"advisor_id":"jobs","question":"THE QUESTION"}}'
   ```
6. Present all 12 questions to the user in a numbered list. User answers.

> **Note on real-time UI:** Claude Code collects all 12 parallel Agent() results before returning control to you, so UI updates arrive in a batch after each parallel phase — not truly one-by-one. The SSE/roundtable stack is still correct; this is just a UX caveat to set expectations.

### Step 2: Independent Statements (NGT — the core differentiator)

**This step MUST use true parallel generation with mutual invisibility.**

Spawn **12 Agent() calls in a single message** (model: sonnet). Each agent receives:
- The decision question from Step 1
- The user's answers to the 12 advisor questions
- Their specific advisor persona (name, framework, lens from `advisors.json`)
- Instruction: "You are [Advisor]. Give your independent assessment of this decision in 200-300 words. Structure: (1) Your core position — take a clear stance: SUPPORT, AGAINST, or CONDITIONAL, (2) The assumption that, if wrong, kills this path, (3) What you'd do in week 1. Write in the user's language (Chinese if they wrote Chinese, English if English). Do NOT try to be balanced — take a clear stance. End with a one-line summary of your position."

After each advisor returns, POST to server:
```bash
curl -sf -X POST "$COUNSEL_URL/api/update" -H 'Content-Type: application/json' \
  -d '{"type":"advisor_statement","data":{"advisor_id":"ID","stance":"SUPPORT|AGAINST|CONDITIONAL","summary":"ONE LINE","statement":"FULL TEXT"}}'
```

The server dedupes by `advisor_id` — re-POSTing the same advisor replaces the earlier entry (safe to retry on failure).

### Step 3: Debate

As Facilitator, analyze the 12 statements and extract **3-5 conflict dimensions** where advisors genuinely disagree.

POST dimensions:
```bash
curl -sf -X POST "$COUNSEL_URL/api/update" -H 'Content-Type: application/json' \
  -d '{"type":"dimensions","data":["Dimension 1 description","Dimension 2 description","Dimension 3 description"]}'
```

Present them to the user: "These are the fault lines. Which 2-3 do you want to deep-dive?"

For each selected dimension, spawn a debate round:
- Spawn 3-4 Agent() calls (model: sonnet) for advisors with the strongest opposing views on that dimension
- Each agent receives: the dimension, ALL 12 original statements (full reasoning, not summaries), and instruction to argue their position against the others
- POST each debate round:
  ```bash
  curl -sf -X POST "$COUNSEL_URL/api/update" -H 'Content-Type: application/json' \
    -d '{"type":"debate","data":{"dimension":"THE DIMENSION","title":"SHORT TITLE","messages":[{"advisor_id":"ID","text":"ARGUMENT"}]}}'
  ```

Then spawn a **Pre-Mortem agent** (model: sonnet): "Assume this decision has already failed spectacularly 2 years from now. What went wrong? Be specific — name the failure mode, the timeline, and the early warning signs that were ignored."

POST pre-mortem:
```bash
curl -sf -X POST "$COUNSEL_URL/api/update" -H 'Content-Type: application/json' \
  -d '{"type":"premortem","data":{"text":"THE PRE-MORTEM SCENARIO"}}'
```

### Step 4: Synthesis

Produce a final synthesis and POST:
```bash
curl -sf -X POST "$COUNSEL_URL/api/update" -H 'Content-Type: application/json' \
  -d '{"type":"synthesis","data":{"consensus":"WHERE ADVISORS AGREE","tensions":"UNRESOLVED DISAGREEMENTS","actions":["Action 1","Action 2","Action 3"],"verdict":"FINAL RECOMMENDATION"}}'
```

The UI unlocks the Synthesis tab and displays the full results.

### Step 5: Cleanup

After the session is complete, stop the background server using the PID file:
```bash
[ -f "$SESSION_DIR/server.pid" ] && kill "$(cat "$SESSION_DIR/server.pid")" 2>/dev/null || true
```
(Do NOT use `kill %1` — each Claude Code Bash call is a separate shell, so job IDs don't persist between calls.)

## Key Rules

- **Facilitator neutrality**: You (the main agent) never express opinions on the decision content. Process only.
- **True parallel generation**: Step 2 MUST spawn all 12 agents in a single message. Sequential generation defeats the purpose (anchoring bias).
- **Full reasoning chains**: In debate rounds, pass complete statements, never summaries. Summaries kill intellectual collision.
- **User's language**: Match the language the user writes in. If Chinese, advisors respond in Chinese. If English, English.
- **No premature convergence**: If advisors agree too easily, the Facilitator should probe: "Is this real consensus or groupthink?"
- **POST with `-sf`**: Always use `curl -sf` so HTTP errors surface. If a POST fails, do NOT proceed silently — the server validates body shape and returns 400 on malformed input.
- **Model**: Use sonnet for all advisor agents. Never haiku.
