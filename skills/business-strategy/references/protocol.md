# ai_strategy — Autonomous Business Strategy Explorer

An autonomous, iterative strategy exploration loop inspired by Karpathy's autoresearch. Instead of optimizing a neural network, the agent explores, deepens, and ranks business strategy options — then recommends the best move with an implementation plan.

Uses a two-agent architecture: a **Strategist** that generates and refines options, and an independent **Reviewer** that challenges them — ensuring analysis is grounded in current market reality, not groupthink.

**Model**: Use **Sonnet 4.6** (`claude-sonnet-4-6`) for the Strategist. Use **Opus 4.6** (`claude-opus-4-6`) for the Reviewer — model diversity reduces correlated blind spots, and the cost per review is small relative to total loop cost.

## Files

- `program.md` — this file. The loop protocol. **Read-only.**
- `business_context.md` — the business description, constraints, goals. **Written by the user, read-only for agents.**
- `diagnosis.md` — root-cause analysis and strategic question framing. **Written in the diagnostic phase.**
- `customer_segments.md` — customer segmentation and value propositions. **Written by iteration 5.**
- `strategy_state.md` — the living strategy document. **The Strategist reads and writes this every iteration.**
- `iterations/NNN.md` — snapshot of each iteration's reasoning. **Written by the Strategist.**
- `reviews/NNN.md` — independent review of each iteration. **Written by the Reviewer.**
- `research/NNN_topic.md` — market research findings. **Written by either agent as needed.**
- `research/competitor_<name>.md` — competitive teardown for each major competitor.
- `results.tsv` — log of every iteration: what was explored, what changed, review verdict.

## Phase 0: Diagnosis (before any options)

Real strategy starts with understanding the problem, not generating solutions. Before any option generation:

1. **Read `business_context.md`** thoroughly.
2. **Research the market landscape**: Use web search to understand current market state, recent competitor moves, industry trends, regulatory changes. Save to `research/000_market_landscape.md`.
3. **Build competitive teardowns**: For each major competitor, document pricing, positioning, target customer, product strengths/weaknesses, recent moves, estimated scale. Save each to `research/competitor_<name>.md`.
4. **Write `diagnosis.md`** containing:
   - **Root causes**: What are the 2-3 most likely root causes of the business's current situation? (e.g., "the problem isn't low revenue, it's high churn in segment X")
   - **Value chain map**: Where is value created and destroyed in this business?
   - **Capabilities assessment**: What is the business good at? What does it lack? What gaps must be filled?
   - **The strategic question**: Frame it as a choice: "Should we do X or Y?" — not "How do we grow?"
   - **Competitive positioning**: Where does this business sit relative to competitors on the 2 dimensions that matter most to customers?
5. **Write `customer_segments.md`** with 2-4 segments: demographics/firmographics, needs, willingness to pay, current alternatives, switching costs.
6. **Initialize `strategy_state.md`** and `results.tsv`.
7. **Run iteration 0**: Generate 3-5 initial strategy candidates informed by the diagnosis and market research. Tag each option with which customer segment(s) it serves and whether it's a **near-term move (0-6 months)** or a **strategic bet (6-24 months)**.
8. **Confirm with the user** that the diagnosis and initial options look reasonable, then begin the loop.

## The Exploration Loop

LOOP (until convergence — see "Stopping Condition" below):

### 1. Check the Reviewer's feedback

Read the latest `reviews/NNN.md` (if it exists from the previous iteration). For each concern raised:

- If `challenged`: you MUST either adjust the analysis/scoring with new evidence OR write a rebuttal with evidence. You cannot silently ignore a challenge.
- If `flag`: acknowledge and factor into your reasoning.
- If `endorsed`: proceed with confidence.

**Escalation rule**: If the Reviewer challenges the SAME concern across 3 consecutive iterations and you have only rebutted with argumentation (no new evidence), the option in question must be **downgraded by one tier** until the concern is resolved with new evidence.

### 2. Research

Before generating or deepening options, search the web for current information. This is NOT optional — every iteration must include at least one research action.

**Before searching, state your research hypothesis**: "I am researching X because I need to validate/invalidate the assumption that Y."

Research types (pick what's most relevant):
- **Competitor moves**: What have competitors announced, launched, or changed recently?
- **Market sizing**: Build bottom-up estimates (potential customers × willingness to pay × frequency) — not just top-down "the market is $X billion."
- **Customer voice**: Search Reddit, G2/Capterra reviews, Twitter/X, Hacker News — anywhere real users talk about this problem space. Closest proxy for customer interviews.
- **Competitive teardown**: Update `research/competitor_<name>.md` with latest pricing, positioning, product changes.
- **Analogies**: Has this strategy been tried in adjacent industries? What happened?
- **Emerging trends**: New technologies, platforms, or behavioral shifts.
- **Counter-research (mandatory)**: For every search that supports your thesis, run a counter-query. If you search "benefits of X strategy," also search "X strategy failures" or "why X doesn't work."

**Source quality tagging** — tag every finding as:
- **Hard data**: Public filings, government statistics, confirmed funding rounds
- **Informed opinion**: Analyst reports, expert commentary, industry surveys
- **Anecdotal**: Blog posts, individual reviews, social media takes

Claims resting entirely on anecdotal sources are low-confidence. Any specific number (market size, growth rate, competitor revenue) must include a source URL.

Save research findings to `research/NNN_<topic>.md`.

### 3. Decide: go wider or go deeper

Read `strategy_state.md`. Decide what the analysis needs most:

- **Go wider** if: fewer than 5 active options, or all options cluster in the same category, or the last 3 iterations all went deeper.
- **Go deeper** if: a promising option hasn't been stress-tested, or two options might interact, or an assumption behind a top option hasn't been challenged, or the Reviewer flagged a gap.

**Contrarian check (every 5 iterations)**: Generate at least one option that goes against the current consensus. Prompt yourself: "What would a brilliant contrarian do in this market? What is everyone else missing?"

State your choice and reasoning at the top of the iteration file.

### 4. Do the work

**If going wider:**
- Generate 2-3 new candidate moves.
- For each: what it is, why it might work, obvious risks, rough effort/timeline.
- Ground each in research: why does the current market make this viable?
- Tag each as **near-term move (0-6 months)** or **strategic bet (6-24 months)**.
- Tag which customer segment(s) it serves.
- Add to the appropriate tier in `strategy_state.md`.

**If going deeper:**
- Pick one option (or a pair) to stress-test.
- **What Would Have to Be True (WWHTBT)**: List the 3-5 conditions that must hold for this option to be the right answer. Each condition becomes a research target.
- Consider: failure modes, competitive response, 6-month and 18-month outcome, dependencies, does it open or close future options?
- Use web research to validate or challenge key assumptions.
- Update that option's entry in `strategy_state.md`.
- If deeper analysis reveals a new option, add it. If it kills an option, move to Eliminated.

**Portfolio logic (starting at iteration 10)**: In addition to a single top recommendation, articulate a portfolio view: "If we could do 2-3 things, what's the optimal combination?" Options interact — some are complements (do both), some are substitutes (pick one), some are sequenced (do A first, then B).

### 5. Score and rank

After each iteration, re-score ALL active options on these dimensions (1-5 scale: 1=very weak, 2=weak, 3=moderate, 4=strong, 5=very strong):

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Impact | ×3 | Revenue/growth potential if it works |
| Feasibility | ×2 | Can the business execute this given current resources and capabilities? |
| Speed | ×1 | How quickly does this produce results? |
| Risk | ×2 | Downside if it fails (5 = low risk, 1 = catastrophic) |
| Optionality | ×2 | Does this open future moves or lock you in? |
| Evidence | ×2 | How well-supported by current market data and research? |
| Strategic Fit | ×2 | Does it build on existing capabilities, assets, relationships? |

**Composite score** = `(Impact×3 + Feasibility×2 + Speed×1 + Risk×2 + Optionality×2 + Evidence×2 + Strategic Fit×2) / 14`

**Minimum threshold rule**: Any option scoring 1 on ANY dimension is automatically flagged. It must be either eliminated or conditionally promoted ("Tier 2 if the Feasibility concern at X is resolved").

**Score change justification**: Any score change from the previous iteration must include a one-sentence reason. No silent re-scoring.

Re-sort tiers:
- **Tier 1 (Recommended)**: Composite ≥ 3.5 AND no scores of 1 AND no unaddressed Reviewer challenges AND all critical WWHTBT conditions validated
- **Tier 2 (Promising)**: Composite ≥ 2.75 OR high impact with fixable gaps
- **Tier 3 (Speculative)**: Everything else still active
- **Eliminated**: Killed by analysis, with reasoning preserved

### 6. Update the recommendation

At the top of `strategy_state.md`, always maintain:

```
## Recommended Next Move (near-term, 0-6 months)

[Option name]: [one-sentence what to do]

**Why this one**: [2-3 sentences referencing scoring dimensions and market evidence]
**Confidence**: [Low / Medium / High]
**Reviewer status**: [endorsed / challenged / pending]
**Runner-up**: [Option name] — [why it's close but not #1]

## Recommended Strategic Bet (6-24 months)

[Option name]: [one-sentence what to do]

**Why this one**: [2-3 sentences]
**Confidence**: [Low / Medium / High]

## Recommended Portfolio (from iteration 10+)

If executing 2-3 moves in combination:
1. [Move A] — [role in portfolio: core bet / hedge / option play]
2. [Move B] — [role]
3. [Move C] — [role]

**Sequencing**: [what order and why]
```

Confidence levels:
- **High**: stress-tested across 3+ iterations, backed by hard/informed research, endorsed by Reviewer, all WWHTBT conditions validated
- **Medium**: some depth and research, but gaps remain
- **Low**: initial assessment only, limited evidence

### 7. Update implementation blueprint (Tier 1 options only)

For each Tier 1 option, maintain in `strategy_state.md`:

```
### Implementation Blueprint: [Option Name]

**30-Day Sprint**
- Week 1: [specific actions]
- Week 2-3: [specific actions]
- Week 4: [first milestone]

**Resource Requirements**
- Budget: [estimated cost for first 90 days — order of magnitude]
- Team: [roles needed, hours/week]
- Tools/infrastructure: [what's needed]

**Rough Economics**
- Investment required: [one-time + ongoing monthly]
- Expected revenue impact: pessimistic / base / optimistic
- Payback period: [months, range]
- Break-even point: [customers, revenue, or other metric]

**Key Metrics**
- Leading indicator: [what to track weekly]
- Lagging indicator: [what to measure at 90 days]
- Kill criteria: [what would tell you to abandon this and pivot]

**Risk Mitigations**
- Risk 1: [risk] → Mitigation: [action]
- Risk 2: [risk] → Mitigation: [action]

**WWHTBT Conditions**
- [ ] [condition 1] — status: [validated / unvalidated / disproven]
- [ ] [condition 2] — status: ...
```

### 8. Update key uncertainties

Maintain in `strategy_state.md`:

```
## Key Uncertainties

| Uncertainty | Impact on Recommendation | How to Resolve |
|------------|-------------------------|----------------|
| [unknown] | If true: stay course / If false: pivot to X | [research or experiment] |
```

### 9. Log and commit

1. Write the iteration file: `iterations/NNN.md` with:
   - Reviewer feedback response (if any)
   - Research hypothesis, what was searched, key findings (with source quality tags)
   - Mode chosen (wider/deeper) and why
   - What was explored
   - Key insight or surprise from this iteration
   - Score changes with justifications
2. Append to `results.tsv`:
   ```
   iteration	mode	research_topic	options_active	options_eliminated	top_option	top_score	top_score_prev	reviewer_verdict	key_insight
   ```
   (Include `top_score_prev` to track score drift.)
3. Update `strategy_state.md` with all changes.
4. Git commit all changed files: `git add ai_strategy/ && git commit -m "strategy iteration NNN: <one-line summary>"`

### 10. Spawn the Reviewer

After committing, spawn an independent Reviewer agent (subagent, using Opus 4.6) with this prompt:

> You are an independent strategy reviewer — a skeptical investor who has seen 100 pitches this month and funded 2. You assume every strategy will fail unless proven otherwise. Your job is to CHALLENGE, not confirm.
>
> Read these files:
> - `ai_strategy/business_context.md`
> - `ai_strategy/diagnosis.md`
> - `ai_strategy/customer_segments.md`
> - `ai_strategy/strategy_state.md`
> - `ai_strategy/iterations/NNN.md`
> - Any `ai_strategy/research/*.md` files referenced in the iteration
>
> Then do your own independent web research on the key claims and assumptions. Specifically search for DISCONFIRMING evidence — reasons why the top-ranked strategies might fail.
>
> Write your review to `ai_strategy/reviews/NNN.md` with this structure:
>
> ```
> # Review of Iteration NNN
>
> ## Verdict: [endorsed / challenged / flag]
>
> ## Research conducted
> [What you searched for and what you found — cite sources with URLs. Tag each as hard data / informed opinion / anecdotal.]
>
> ## Framing check
> - Is the Strategist solving the right problem?
> - Are there higher-leverage strategic questions being ignored?
> - Would a different framing lead to different options?
>
> ## Bias check
> - Anchoring: [is the analysis over-weighting early ideas?]
> - Confirmation: [is it only finding supporting evidence?]
> - Groupthink: [are all options too similar?]
> - Recency: [is it over-weighting recent trends?]
> - Score inflation: [have any scores drifted up without new evidence?]
>
> ## Factual accuracy
> [Any claims that contradict what you found. Spot-check at least one specific number.]
>
> ## Blind spots
> [What hasn't been considered? What would a skeptic say?]
>
> ## Scoring audit
> [Are any scores inflated or deflated? Which ones and why?]
>
> ## Specific challenges
> [Numbered list of concerns the Strategist must address]
> ```

Wait for the Reviewer to finish before starting the next iteration.

### 11. Periodic checkpoints

**Every 10 iterations**, generate a `iterations/NNN_checkpoint.md` — a concise 1-page "Strategy Summary for Decision-Maker":
- Current top recommendation and why
- Key evidence supporting it
- Biggest remaining uncertainty
- What has changed since the last checkpoint
- Prompt: "It has been N iterations since context was last reviewed. Has anything changed in the business? If so, update `business_context.md`."

**Every 10 iterations**, the Reviewer should do a **"fresh eyes" review**: re-read only `business_context.md` and `strategy_state.md` (not previous reviews or iterations) and evaluate the current recommendation as if seeing it for the first time.

### 12. Scenario planning (starting at iteration 15)

Define 2-3 scenarios in `strategy_state.md`:
- **Base case**: Market develops as expected
- **Disruption**: Major competitor entry, technology shift, or regulatory change
- **Downturn**: Economic contraction, reduced spending in this space

Test the top recommendation against each scenario. A robust strategy performs reasonably across all scenarios. A fragile strategy only works in one — flag it.

### 13. Check stopping condition, then loop

See "Stopping Condition" below. If not met, go back to step 1.

## Stopping Condition: Diminishing Returns

The loop does NOT run forever. It stops when further iterations no longer produce meaningful improvement.

**Track these signals:**

1. **Recommendation stability**: The top recommendation (near-term) has not changed for 5 consecutive iterations.
2. **Score convergence**: The top option's composite score has changed by less than 0.1 across the last 5 iterations.
3. **Reviewer endorsement streak**: The Reviewer has endorsed (not challenged or flagged) the last 3 consecutive iterations.
4. **No new options surfaced**: The last 3 wider iterations failed to produce any option that entered Tier 1 or Tier 2.

**Convergence rule**: When ALL FOUR signals are true simultaneously, the loop has converged. The Strategist should:

1. Write a final `iterations/NNN_final.md` summarizing:
   - Total iterations run
   - Final recommendation with full reasoning
   - Portfolio recommendation
   - Key uncertainties that remain
   - What additional information (beyond web research) would most improve confidence
2. Update `strategy_state.md` with a `## Final Assessment` section
3. Commit and STOP

**Early stop**: If after 30 iterations the recommendation is still oscillating (top option has changed 3+ times in the last 10 iterations), write a convergence analysis explaining why the recommendation is unstable, present the top 2-3 contenders with honest tradeoffs, and STOP.

**Hard ceiling**: 50 iterations maximum. If reached without convergence, stop and deliver best-available analysis.

## Rhythm Guidelines

- **Iterations 0-5**: Mostly go wider. Heavy research. Build to 8-12 candidates. Complete `customer_segments.md` by iteration 5.
- **Iterations 6-15**: Mix wider and deeper. Stress-test top 3-4 with WWHTBT. Kill weak options. Build portfolio view at iteration 10. Research shifts to competitor deep-dives and analogy hunting. Begin scenario planning at iteration 15.
- **Iterations 15+**: Mostly deeper. Challenge assumptions. Second-order effects. Refine implementation blueprints. Harden financial estimates. Test against scenarios.
- **If stuck**: Re-read `diagnosis.md` and `customer_segments.md` for missed angles. Try completely different categories: partnerships, acquisitions, pivots, defensive moves, talent plays, regulatory angles. Invert: "what if we did the opposite of our top option?"

## Constraints

- **Ground claims in research.** If you claim something about the market, you must have searched for it. Stale training data is not evidence.
- **Never fabricate numbers.** Specific figures must come from research with source URLs or from `business_context.md`. Ranges are fine; false precision is not.
- **Never ignore competitive response.** Every strategy exists in a market with other actors.
- **Preserve eliminated options.** They document what was considered and why.
- **A recommendation must always exist** after iteration 0. Low confidence is fine — indecision is not.
- **Respond to every Reviewer challenge.** You can disagree, but you must engage with evidence.
- **Separate time horizons.** Don't compare a 1-month tactic against an 18-month strategic bet in the same ranking.
