# Consultant Review: ai_strategy Autonomous Strategy Explorer

**Reviewer**: Independent strategy critique (McKinsey/BCG-caliber lens)
**Date**: 2026-03-17
**Scope**: Full review of process design, scoring model, research methodology, reviewer architecture, output quality, and failure modes

---

## Executive Summary

This is an ambitious and well-structured system that correctly identifies several things most AI strategy tools get wrong: the need for iterative deepening, independent challenge, grounding in current market data, and the discipline of maintaining a living recommendation. The two-agent architecture (Strategist + Reviewer) is the single strongest design choice and puts this ahead of most AI strategy tools.

However, viewed through the lens of how top consulting firms actually execute strategy engagements, there are significant gaps in diagnostic rigor, customer-centricity, financial modeling, implementation planning, and stakeholder management. The system is stronger at option generation than at the disciplined narrowing and economic validation that separates a "list of good ideas" from an actionable strategy.

Below is a detailed critique across seven dimensions, with specific, actionable recommendations for each.

---

## 1. Process Rigor

### What works well

- The wider-then-deeper rhythm (iterations 0-5 wide, 6-15 mixed, 15+ deep) mirrors how real strategy work flows from divergent to convergent thinking.
- The mandate to "never stop" and produce 30+ iterations is clever — it forces the system past the shallow "first good idea" problem that plagues most AI-generated strategy.
- The constraint that a recommendation must always exist after iteration 0 is excellent. It prevents analysis paralysis and forces the system to commit under uncertainty, which is how real strategy operates.

### What's missing

**a) No diagnostic phase before option generation.**

Top firms spend 20-40% of an engagement on problem definition and diagnosis before they generate a single option. The current flow goes: read context -> research market -> generate options. This skips the critical step of asking "what is the *actual* strategic question we're solving?" A business that says "I want to grow revenue" might actually have a retention problem, a pricing problem, or a positioning problem. The loop jumps to solutions without diagnosing root causes.

**Recommendation**: Add an "Iteration -1" diagnostic phase between Setup steps 1 and 2. The Strategist should:
- Identify the 2-3 most likely root causes of the business's current situation
- Map the business's current value chain and identify where value is created and destroyed
- Articulate the strategic question as a choice: "Should we do X or Y?" not "How do we grow?"
- Write a `diagnosis.md` file that the Strategist references throughout the loop

**b) No structured hypothesis testing.**

McKinsey's core methodology is hypothesis-driven: form a hypothesis, design analyses to prove or disprove it, then iterate. The current system generates options and scores them, but doesn't formally state "what would have to be true for Option X to be the right answer?" and then systematically test each condition.

**Recommendation**: For each Tier 1 and Tier 2 option, require an explicit "What Would Have to Be True" (WWHTBT) list — a technique Roger Martin and A.G. Lafley popularized from their P&G/Monitor work. Each condition becomes a research task. An option is only Tier 1 when all critical conditions have been validated.

**c) No portfolio logic.**

The system treats options as independent alternatives, but real strategy often involves portfolios: a core bet, a hedging move, and an option play. The current "pick one recommendation" framing misses combinations.

**Recommendation**: After iteration 10, require the Strategist to articulate a portfolio view: "If we could do 2-3 things, what's the optimal combination?" This accounts for the fact that options interact — some are complements (do both), some are substitutes (pick one), and some are sequenced (do A first, then B).

---

## 2. Scoring Model

### What works well

- The six dimensions cover a reasonable spread of strategic considerations.
- The weighting toward Impact, Feasibility, and Evidence is sound — it penalizes "brilliant but impossible" and "plausible but ungrounded."
- The tier system with explicit thresholds (7.0, 5.5) provides clear decision rules.

### Problems

**a) The composite score is a weighted average, which hides fatal flaws.**

A strategy that scores Impact=10, Feasibility=1 gets a composite of ~4.8, placing it in Tier 3. But a strategy that scores Impact=5, Feasibility=5 across the board gets a 5.0 and also lands in Tier 3. These are fundamentally different situations — one is a moonshot with an execution barrier, the other is mediocre on all fronts. A weighted average treats them identically.

**Recommendation**: Add a "minimum threshold" rule: any option scoring below 3 on *any* dimension is automatically flagged for elimination or conditional promotion ("this is Tier 1 *if* the Feasibility concern at X is resolved"). Real consulting uses "must-haves" alongside "nice-to-haves."

**b) The Evidence dimension conflates two things.**

"How well-supported is this by current market data?" blends (i) whether the market opportunity is real with (ii) whether the execution approach has precedent. These should be separated. A strategy could target a well-documented market opportunity (high evidence) using an unproven execution model (low evidence), or vice versa.

**Recommendation**: Split Evidence into two dimensions:
- **Market validation**: Is there evidence the demand/opportunity exists? (TAM data, customer signals, analogues)
- **Execution precedent**: Has this approach worked for comparable companies? Are there case studies or analogues?

**c) The scoring scale (1-10) invites false precision.**

Asking an AI to distinguish between a 6 and a 7 on "Optionality" is theater. The model will confidently assign numbers that imply a precision the analysis doesn't support, and the composite score will be taken as more reliable than it is.

**Recommendation**: Switch to a 3-point or 5-point scale (Low / Medium / High, or 1-3-5-7-9). This forces meaningful differentiation without false precision. Alternatively, keep the 1-10 scale but require that any score change of 1 point must be justified with a specific reason in the iteration file. No silent re-scoring.

**d) The scoring formula in `strategy_state.md` is inconsistent with `program.md`.**

`program.md` defines 6 dimensions with a divisor of 12: `(Impact x 3 + Feasibility x 2 + Speed x 1 + Risk x 2 + Optionality x 2 + Evidence x 2) / 12`. But `strategy_state.md` lists only 5 dimensions (no Evidence) with a divisor of 10. This is a bug that will cause confusion.

**Recommendation**: Fix `strategy_state.md` to match `program.md`. This is a straightforward consistency issue.

**e) No weighting for strategic fit.**

The dimensions measure an option in isolation but don't assess how well it fits the specific business's capabilities, culture, and existing strategic direction. A Feasibility score partially captures this, but a McKinsey engagement would explicitly score "degree of strategic fit" — does this leverage what we're already good at, or does it require building entirely new capabilities?

**Recommendation**: Add a "Strategic Fit" dimension (weight x2): Does this option build on existing capabilities, assets, and relationships? Or does it require the business to become a fundamentally different company?

---

## 3. Research Methodology

### What works well

- Mandating research every iteration is the right call. Most AI strategy tools hallucinate market data.
- The research targets list (competitor moves, market data, customer signals, analogies, emerging trends) covers the main categories.
- Saving research to versioned files creates an audit trail.

### What's missing

**a) No primary research, only secondary.**

The system relies entirely on web search — which means it only sees published, public information. A real consultant would conduct:
- **Customer interviews** (even 5 conversations reveal more than 50 web searches)
- **Expert calls** (1-hour call with an industry veteran beats a week of desk research)
- **Competitive intelligence** through product teardowns, pricing analysis, mystery shopping
- **Financial modeling** from public filings, not just qualitative "the market is growing"

The system cannot do interviews, but it *can* do better secondary research.

**Recommendation**:
- Add a research type: **quantitative market sizing**. Force the Strategist to build a bottom-up market size estimate (number of potential customers x willingness to pay x frequency) rather than relying on top-down "the market is $X billion" figures from analyst reports.
- Add a research type: **competitive teardown**. For each major competitor, document: pricing, positioning, target customer, product strengths/weaknesses, recent moves, estimated scale. Store as `research/competitor_<name>.md`.
- Add a research type: **customer voice**. Search for Reddit threads, G2/Capterra reviews, Twitter/X complaints, Hacker News discussions — anywhere real users talk about the problem. This is the closest proxy for interviews the system can access.
- Add explicit prompting to the Reviewer to search for *disconfirming* evidence specifically. The current prompt says "challenge" but doesn't mandate searching for evidence that contradicts the Strategist's thesis.

**b) No research quality assessment.**

Not all web sources are equal. A TechCrunch article about a funding round is a fact. A Medium blog post about "the future of X" is an opinion. A Gartner report is expensive conventional wisdom. The system doesn't distinguish between these.

**Recommendation**: Require the Strategist and Reviewer to tag each research finding with a confidence level:
- **Hard data**: Public filings, government statistics, confirmed funding rounds
- **Informed opinion**: Analyst reports, expert commentary, industry surveys
- **Anecdotal**: Blog posts, individual reviews, social media takes

Any claim that rests entirely on "anecdotal" sources should be flagged as low-confidence.

**c) The research is unstructured.**

"Search the web for current information relevant to this iteration's focus" is too vague. Real consultants design research around specific hypotheses.

**Recommendation**: Before each research phase, the Strategist should state: "I am researching X because I need to validate/invalidate the assumption that Y." This turns research from exploration into targeted hypothesis testing.

---

## 4. Reviewer Design

### What works well

- The independent Reviewer is the system's best feature. The separation of concerns (Strategist creates, Reviewer challenges) mirrors the partner review process at top firms.
- The structured review template (bias check, factual accuracy, blind spots, scoring audit) is well-designed.
- The mandate that the Strategist must respond to every challenge prevents the "ignore the critic" failure mode.
- Checking for specific biases (anchoring, confirmation, survivorship, recency) is thoughtful.

### Problems

**a) The Reviewer has no teeth.**

The Reviewer can say "challenged," but the Strategist can write a rebuttal and move on. There's no mechanism for escalation. If the Reviewer challenges the same issue three times and the Strategist rebuts three times, the system has no way to resolve the deadlock.

**Recommendation**: Add an escalation rule: if the Reviewer challenges the same concern across 3 consecutive iterations, the option in question must be downgraded by one tier until the concern is resolved with new evidence (not just argumentation). This gives the Reviewer real power.

**b) The Reviewer uses the same model as the Strategist.**

Both agents run on Sonnet 4.6. LLMs have systematic biases — overconfidence, tendency toward conventional wisdom, difficulty with truly contrarian analysis. Using the same model for both roles means the Reviewer will share the Strategist's blindspots.

**Recommendation**: Consider using a different model for the Reviewer (e.g., Opus 4.6 for Reviewer while Strategist stays on Sonnet 4.6). The cost per review is small relative to the total loop cost, and model diversity reduces correlated failure. Alternatively, give the Reviewer a strongly contrarian system prompt: "You are a skeptical investor who has seen 100 pitches this month and funded 2. You assume every strategy will fail unless proven otherwise."

**c) The Reviewer cannot challenge the framing, only the content.**

The Reviewer sees the Strategist's output and challenges specific claims. But what if the entire problem framing is wrong? What if the business should be asking a different strategic question? The Reviewer's template doesn't include a "framing check."

**Recommendation**: Add a section to the review template:

```
## Framing check
- Is the Strategist solving the right problem?
- Are there higher-leverage strategic questions being ignored?
- Would a different framing of the business's situation lead to different options?
```

**d) No external validation mechanism.**

The Reviewer challenges the Strategist, but who challenges the Reviewer? In a real firm, there's a hierarchy: associate -> engagement manager -> partner -> client. Here, it's just two agents in a closed loop.

**Recommendation**: Every 10 iterations, generate a "Strategy Summary for Decision-Maker" — a concise 1-page brief designed to be read by the business owner. This forces the system to translate its analysis into terms a non-consultant can evaluate, and gives the user natural checkpoints to intervene.

---

## 5. Output Quality

### What works well

- The `strategy_state.md` living document is a good idea — a single source of truth that evolves.
- Preserving eliminated options with reasoning is valuable (shows thoroughness, prevents re-treading).
- The recommendation format (what, why, confidence, reviewer status, runner-up) gives the reader the essentials.

### Problems

**a) The deliverable is a strategy document, not a decision document.**

`strategy_state.md` tells you what was analyzed and what scored highest. It does not tell you:
- What specific actions to take on Monday morning
- How much it will cost
- What the expected return is
- What the timeline looks like
- What you should stop doing to free up resources
- Who is responsible for what
- What the first 30 days look like

A McKinsey final deliverable is not "here are ranked options." It is "here is what you should do, here is the implementation plan, here are the economics, and here are the risks with mitigations."

**Recommendation**: Add an "Implementation Blueprint" section to `strategy_state.md` for the top recommendation:

```
## Implementation Blueprint

### 30-Day Sprint
- Week 1: [specific actions]
- Week 2-3: [specific actions]
- Week 4: [specific actions, first milestone]

### Resource Requirements
- Budget: [estimated cost for first 90 days]
- Team: [roles needed, hours/week]
- Tools/infrastructure: [what's needed]

### Key Metrics
- Leading indicator: [what to track weekly]
- Lagging indicator: [what to measure at 90 days]
- Kill criteria: [what would tell you to abandon this and pivot]

### Risk Mitigations
- Risk 1: [risk] -> Mitigation: [action]
- Risk 2: [risk] -> Mitigation: [action]
```

**b) No financial model, even a rough one.**

The scoring system is qualitative. A business owner needs to know: "If this works, what's the expected revenue impact? What's the investment required? What's the payback period?" Even rough estimates (order of magnitude) are more useful than a score of "Impact: 8."

**Recommendation**: For Tier 1 options, require a rough financial estimate:
- Investment required (one-time + ongoing monthly)
- Expected revenue impact (range: pessimistic / base / optimistic)
- Payback period (months)
- Break-even point (customers, revenue, or other relevant metric)

These don't need to be precise — ranges are fine. But they need to exist. A business owner comparing "Strategy A: invest $5K, expect $2K/month in 6 months" vs "Strategy B: invest $20K, expect $10K/month in 3 months" can make a decision. A business owner comparing "Impact: 8" vs "Impact: 7" cannot.

**c) No "what we don't know" section.**

The output should explicitly state what remains uncertain and what additional information would change the recommendation. This is standard in consulting deliverables: "Our recommendation is X. This is contingent on assumptions A, B, and C. If assumption B is wrong, we would recommend Y instead."

**Recommendation**: Add a "Key Uncertainties" section to `strategy_state.md`:

```
## Key Uncertainties

| Uncertainty | Impact on Recommendation | How to Resolve |
|------------|-------------------------|----------------|
| [unknown] | If true: stay course / If false: pivot to X | [research or experiment needed] |
```

---

## 6. What's Missing Entirely

### a) Customer segmentation and value proposition analysis

The system generates strategy options but never formally segments the customer base or maps value propositions. This is foundational in consulting — you cannot set strategy without understanding *which customers* you're targeting and *what specific value* you're offering them.

**Recommendation**: Add a required artifact: `customer_segments.md`. Before iteration 5, the Strategist should define 2-4 customer segments with: demographics/firmographics, needs, willingness to pay, current alternatives, and switching costs. Every strategy option should be tagged with which segment(s) it serves.

### b) Competitive positioning map

The system researches competitors but never builds a formal competitive positioning map. Where does this business sit relative to competitors on the dimensions that matter to customers?

**Recommendation**: Require a 2x2 positioning map (or similar visual framework) by iteration 5, saved as a structured table in `research/competitive_positioning.md`. The two axes should be the dimensions most relevant to customer choice in this market.

### c) Capabilities assessment

The system scores "Feasibility" but never formally assesses what the business is actually good at and what it lacks. A real engagement includes a capabilities audit.

**Recommendation**: In the diagnostic phase, map the business's key capabilities (what it does well) and key gaps (what it lacks). Each strategy option should explicitly state which capabilities it leverages and which gaps it requires filling.

### d) Scenario planning

The system optimizes for "the most likely future" but doesn't consider alternative futures. What if a recession hits? What if a major competitor enters? What if regulation changes?

**Recommendation**: By iteration 15, require the Strategist to define 2-3 scenarios (e.g., "market grows as expected," "major disruption occurs," "downturn/contraction"). Test the top recommendation against each scenario. A robust strategy performs reasonably across scenarios; a fragile strategy only works in one.

### e) Stakeholder and organizational readiness

Strategy that the organization cannot or will not execute is worthless. The system never considers: Does the team have the skills? Is there organizational resistance? Does the culture support this kind of change?

**Recommendation**: Add an "Organizational Readiness" field to the business context template: team strengths, skill gaps, cultural norms, past change efforts and their outcomes. The Strategist should factor this into Feasibility scoring.

### f) Time-horizon separation

The system mixes short-term tactics (e.g., "launch a marketing campaign") with long-term strategic moves (e.g., "enter a new market segment") in the same tier list. These operate on different timescales and shouldn't be compared directly.

**Recommendation**: Separate options into "near-term moves (0-6 months)" and "strategic bets (6-24 months)." Recommend one of each. A business needs both a "what to do now" and a "where to head."

---

## 7. Risk of Failure Modes

### a) Convergence on conventional wisdom

Both agents have the same training data. Web search surfaces mainstream opinions. The system is likely to converge on the same "obvious" strategies that every business in the space is already pursuing. True strategic advantage comes from non-obvious moves.

**Mitigation**: Every 5 iterations, force a "contrarian iteration" where the Strategist must generate at least one option that goes against the current consensus. Prompt: "What would a brilliant contrarian do in this market? What is everyone else missing?"

### b) Circular reasoning between Strategist and Reviewer

The Strategist writes an analysis. The Reviewer challenges it. The Strategist rebuts. The Reviewer accepts the rebuttal. Over many iterations, the two agents may develop a shared worldview that is internally consistent but disconnected from reality. This is the AI equivalent of groupthink.

**Mitigation**: Every 10 iterations, the Reviewer should do a "fresh eyes" review — re-read only `business_context.md` and `strategy_state.md` (not previous reviews or iterations) and evaluate the current recommendation as if seeing it for the first time.

### c) Score inflation over time

As the Strategist invests more iterations in analyzing an option, it becomes psychologically (and computationally) committed. Scores tend to drift upward as more "supporting evidence" is found. This is a well-documented cognitive bias (the IKEA effect — you value things more when you've built them).

**Mitigation**: Log all score changes in `results.tsv` with before/after values. If an option's composite score has increased by more than 1.5 points over 5 iterations without new external evidence, the Reviewer should flag it as potential score inflation.

### d) Research echo chamber

Web search returns results that match the query terms. If the Strategist searches for "benefits of X strategy," it will find articles about the benefits of X strategy. Confirmation bias is baked into the research methodology.

**Mitigation**: For every research query that supports the current thesis, require a counter-query. If the Strategist searches "benefits of content marketing for SaaS," also require "content marketing failures SaaS" or "why content marketing doesn't work." Explicitly instruct the Reviewer to search for *disconfirming* evidence.

### e) Hallucinated specificity

LLMs are notorious for generating plausible-sounding but fabricated statistics. "The market is expected to grow at 23.4% CAGR" might be a hallucination dressed as research. Even with web search, the model might misinterpret or misattribute findings.

**Mitigation**: Require that any specific number (market size, growth rate, competitor revenue) include a source URL. The Reviewer should spot-check at least one specific claim per iteration by independently searching for the same data point.

### f) Infinite loop with no convergence

The system is designed to run forever, but what if the recommendation oscillates? Option A is #1, then B after a challenge, then A again, then B. The user returns after 50 iterations to find no stable answer.

**Mitigation**: Track recommendation stability. If the top recommendation has changed more than 3 times in the last 10 iterations, the Strategist must write a "convergence analysis" explaining why the recommendation is unstable and what additional information would resolve it.

### g) Business context goes stale

The system reads `business_context.md` once at setup and references it occasionally. But for a long-running loop, the business's situation might change — they land a big customer, lose a key employee, or get a partnership offer. The system has no mechanism to incorporate new information.

**Mitigation**: Every 10 iterations, prompt the user (in the iteration file): "It has been N iterations since the last context update. Has anything changed in the business that would affect this analysis? If so, please update `business_context.md`."

---

## Summary of Priority Recommendations

Ranked by impact on output quality:

| Priority | Recommendation | Section |
|----------|---------------|---------|
| 1 | Add a diagnostic phase before option generation | Process |
| 2 | Add implementation blueprint and rough financial estimates to the deliverable | Output |
| 3 | Fix the scoring formula inconsistency between program.md and strategy_state.md | Scoring |
| 4 | Add minimum-threshold scoring rule to catch fatal flaws | Scoring |
| 5 | Require WWHTBT (What Would Have to Be True) for top options | Process |
| 6 | Add counter-research requirement to combat confirmation bias | Research |
| 7 | Add escalation rule for unresolved Reviewer challenges | Reviewer |
| 8 | Add convergence tracking and stability monitoring | Failure Modes |
| 9 | Separate near-term moves from strategic bets | Missing |
| 10 | Add customer segmentation as a required artifact | Missing |
| 11 | Switch to 5-point scoring scale or require justification for 1-point changes | Scoring |
| 12 | Add scenario planning by iteration 15 | Missing |
| 13 | Use a different model for the Reviewer | Reviewer |
| 14 | Add periodic "fresh eyes" review to break circular reasoning | Failure Modes |
| 15 | Add user checkpoint summaries every 10 iterations | Reviewer |

---

## Final Assessment

This system is a **strong foundation** — significantly better than a single-pass "ask the AI for a strategy" approach. The two-agent architecture, mandatory research, and iterative deepening are all genuinely good design decisions.

The core gap is that the system is optimized for **option discovery and ranking** but underinvests in **diagnosis** (understanding the real problem), **economics** (quantifying the opportunity), and **implementation** (making it actionable). A McKinsey engagement spends roughly equal time on all four: diagnose, generate options, evaluate, and plan. This system spends ~80% on generate and evaluate.

The second major gap is **research rigor**. Web search is necessary but not sufficient. The system needs more structured research protocols, source quality assessment, and mandatory disconfirming evidence searches to avoid the echo chamber effect.

Fix those two gaps — add diagnostic and implementation phases, and harden the research methodology — and this becomes a remarkably capable autonomous strategy tool.
