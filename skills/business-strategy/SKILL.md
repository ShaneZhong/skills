---
name: business-strategy
description: "Autonomous business strategy exploration with research-backed recommendations. Use this skill when the user wants help with business strategy, growth planning, competitive analysis, 'what should my business do next', market entry decisions, strategic planning, go-to-market strategy, business model evaluation, or any question about the best strategic move for a business. Also trigger when the user mentions wanting to simulate or explore business options, compare strategic alternatives, or needs a strategic advisor/consultant. Even casual phrases like 'help me figure out my next move' or 'I need a strategy' should trigger this skill."
---

# Business Strategy Explorer

An autonomous, iterative strategy exploration system inspired by Karpathy's autoresearch. Instead of optimizing a neural network, you explore, deepen, and rank business strategy options — producing a research-backed recommendation with an implementation plan.

You act as a two-agent system: a **Strategist** that generates and refines options, and an independent **Reviewer** (subagent) that challenges them. This prevents groupthink and ensures the analysis is grounded in current market reality.

## When to use this skill

Any time the user needs strategic guidance for a business:
- "What should my business do next?"
- "Help me figure out the best growth strategy"
- "I'm starting a company and need to decide my first moves"
- "Compare these strategic options for my business"
- "I need a business advisor / consultant"

## How it works — the big picture

1. **User fills in business context** — who they are, what the business does, constraints, goals
2. **Diagnostic phase** — you research the market and diagnose the real strategic problem before generating any options
3. **Exploration loop** — iteratively generate, research, score, and stress-test strategy options. An independent Reviewer agent challenges every iteration.
4. **Convergence** — the loop stops when recommendations stabilize (diminishing returns), delivering a final strategy with implementation blueprints

The full protocol is detailed below. Read `references/protocol.md` for the complete loop specification including scoring formulas, reviewer prompts, and stopping conditions.

## Setup

When the user triggers this skill:

1. **Create the workspace** — scaffold `ai_strategy/` in the current working directory:
   ```
   ai_strategy/
   ├── business_context.md   (from template — user fills in)
   ├── strategy_state.md     (initialized with empty structure)
   ├── results.tsv           (header row only)
   ├── iterations/
   ├── reviews/
   └── research/
   ```
   Use the templates from `references/templates.md` for `business_context.md` and `strategy_state.md`.

2. **Ask the user to fill in `business_context.md`** — the more detail they provide, the better the analysis. Key sections: what the business does, current state, market, capabilities, constraints, goals. If the user gives you the info conversationally, fill it in for them.

3. **Confirm** the context looks right before proceeding.

## Phase 0: Diagnosis

Real strategy starts with understanding the problem, not generating solutions. Before any option generation:

1. **Research the market landscape** using web search — current market state, competitor moves, industry trends, regulatory changes. Save to `research/000_market_landscape.md`.

2. **Build competitive teardowns** — for each major competitor: pricing, positioning, target customer, strengths/weaknesses, recent moves, estimated scale. Save to `research/competitor_<name>.md`.

3. **Write `diagnosis.md`** containing:
   - **Root causes** (2-3): What's actually driving the business's current situation?
   - **Value chain map**: Where is value created and destroyed?
   - **Capabilities assessment**: What's the business good at? What gaps exist?
   - **The strategic question**: Frame as a choice ("Should we X or Y?"), not a vague goal
   - **Competitive positioning**: Where does this business sit vs. competitors on the 2 dimensions that matter most

4. **Write `customer_segments.md`** with 2-4 segments: demographics/firmographics, needs, willingness to pay, current alternatives, switching costs.

5. **Initialize files** and run iteration 0: generate 3-5 initial candidates informed by the diagnosis. Tag each as **near-term (0-6mo)** or **strategic bet (6-24mo)** and which segments it serves.

6. **Confirm with the user** that the diagnosis and initial options look reasonable, then begin the loop.

## The Exploration Loop

Read `references/protocol.md` for the complete loop specification. Here's the summary:

Each iteration follows this sequence:

### 1. Check Reviewer feedback
Read the latest review. Respond to every challenge with evidence (not just arguments). After 3 unresolved challenges on the same issue, the option gets downgraded one tier.

### 2. Research (mandatory every iteration)
State a research hypothesis before searching. Use web search for: competitor moves, market sizing, customer voice (Reddit/G2/HN), competitive teardowns, analogies, emerging trends. **Counter-research is mandatory** — for every supporting search, run a disconfirming one. Tag sources as hard data / informed opinion / anecdotal.

### 3. Go wider or deeper
- **Wider**: Generate 2-3 new options grounded in research. Tag time horizon and segments.
- **Deeper**: Stress-test with WWHTBT (What Would Have to Be True) — list conditions that must hold, then research each one.
- **Contrarian check every 5 iterations**: Force at least one option that goes against consensus.

### 4. Score and rank (1-5 scale, 7 dimensions)

| Dimension | Weight |
|-----------|--------|
| Impact | ×3 |
| Feasibility | ×2 |
| Speed | ×1 |
| Risk | ×2 |
| Optionality | ×2 |
| Evidence | ×2 |
| Strategic Fit | ×2 |

**Composite** = weighted sum / 14. Tier 1 ≥ 3.5, Tier 2 ≥ 2.75. Any score of 1 = automatic flag. Justify every score change.

### 5. Update recommendation
Always maintain: recommended near-term move, recommended strategic bet, runner-up, confidence level, reviewer status. Starting at iteration 10, add portfolio recommendation (2-3 moves in combination with sequencing).

### 6. Implementation blueprint (Tier 1 only)
30-day sprint, resource requirements, rough economics (investment, revenue impact range, payback period), key metrics, kill criteria, risk mitigations, WWHTBT condition status.

### 7. Log, commit, and spawn Reviewer
Write iteration file, append to results.tsv, update strategy_state.md, git commit. Then spawn the Reviewer as an independent subagent.

## The Reviewer

Spawn as a **separate agent using Opus 4.6** (`model: "opus"`) after every iteration. The Reviewer's persona is a skeptical investor — assumes everything fails unless proven otherwise.

The Reviewer:
- Reads only the output files (not the Strategist's internal reasoning)
- Does its own web research, specifically searching for **disconfirming** evidence
- Checks for biases: anchoring, confirmation, groupthink, recency, score inflation
- Checks the framing: is the Strategist solving the right problem?
- Audits scores and spot-checks at least one specific factual claim
- Gives a verdict: `endorsed`, `challenged`, or `flag`

See `references/protocol.md` for the full Reviewer prompt template.

**Every 10 iterations**, the Reviewer does a "fresh eyes" review — reads only business_context.md and strategy_state.md, ignoring all previous reviews.

## Periodic Checkpoints (every 10 iterations)

Generate a 1-page decision-maker summary: current recommendation, key evidence, biggest uncertainty, what changed. Prompt the user: "Has anything changed in the business? If so, update business_context.md."

## Scenario Planning (starting at iteration 15)

Define 2-3 scenarios (base case, disruption, downturn). Test the top recommendation against each. Flag fragile strategies that only work in one scenario.

## Stopping Condition: Diminishing Returns

The loop stops when ALL FOUR signals are true simultaneously:

1. **Recommendation stability**: Top near-term recommendation unchanged for 5 iterations
2. **Score convergence**: Top score changed by < 0.1 across last 5 iterations
3. **Reviewer endorsement streak**: Last 3 iterations all endorsed
4. **No new viable options**: Last 3 wider iterations produced nothing entering Tier 1 or 2

When converged: write a final summary, update strategy_state.md with a Final Assessment section, commit and stop.

**Early stop at 30 iterations** if the recommendation is still oscillating (changed 3+ times in last 10). Write a convergence analysis with honest tradeoffs.

**Hard ceiling: 50 iterations**. Deliver best-available analysis.

## Key Constraints

- **Ground claims in research.** Stale training data is not evidence. Search the web.
- **Never fabricate numbers.** Cite source URLs for specific figures. Ranges > false precision.
- **Never ignore competitive response.** Every strategy exists in a market with other actors.
- **Preserve eliminated options.** They show thoroughness and prevent re-treading.
- **A recommendation must always exist** after iteration 0. Low confidence is fine — indecision is not.
- **Separate time horizons.** Near-term moves and strategic bets are ranked separately.
