# Templates

Use these when scaffolding the ai_strategy workspace.

## business_context.md

```markdown
# Business Context

<!--
Fill this in before running the strategy loop.
The more specific you are, the better the analysis will be.
The Strategist treats this as read-only — update it yourself if things change.
-->

## What does the business do?

[Describe your product/service, target customer, and how you make money]

## Current state

- **Stage**: [idea / pre-revenue / early revenue / growing / established]
- **Team size**: [number, key roles filled/missing]
- **Revenue**: [rough range or "pre-revenue"]
- **Runway/budget**: [how long can you operate, what can you invest]
- **Existing customers**: [how many, who are they, how did you get them]

## Market

- **Who are the competitors?** [direct and indirect]
- **What's your edge?** [why would someone choose you over alternatives]
- **Market trend**: [growing, shrinking, shifting — any tailwinds or headwinds]

## Capabilities and team strengths

- **What is the team good at?** [technical skills, domain expertise, relationships, assets]
- **What are the key skill gaps?** [what you'd need to hire or outsource]
- **Culture**: [fast-moving / methodical / technical / sales-driven / etc.]
- **Past change efforts**: [have you pivoted before? what happened?]

## Constraints

- **What can't you do?** [budget limits, regulatory, geographic, skill gaps, time pressure]
- **What have you already tried?** [what worked, what didn't]

## Goals

- **Primary goal**: [what does success look like in 6-12 months?]
- **Secondary goal**: [nice to have]
- **What are you optimizing for?** [revenue growth / profitability / market share / learning / survival]

## Anything else the strategist should know?

[Industry quirks, personal preferences, upcoming events, partnerships in discussion, key relationships, etc.]
```

## strategy_state.md

```markdown
# Strategy State

> This file is maintained by the strategy agent. Do not edit manually during a run.

## Recommended Next Move (near-term, 0-6 months)

*Not yet determined — awaiting diagnostic phase.*

## Recommended Strategic Bet (6-24 months)

*Not yet determined — awaiting diagnostic phase.*

## Recommended Portfolio (from iteration 10+)

*Not yet determined.*

---

## Tier 1 — Recommended

*None yet.*

## Tier 2 — Promising

*None yet.*

## Tier 3 — Speculative

*None yet.*

## Eliminated

*None yet.*

---

## Key Uncertainties

| Uncertainty | Impact on Recommendation | How to Resolve |
|------------|-------------------------|----------------|
| *None yet* | — | — |

---

## Scoring Key

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Impact | ×3 | Revenue/growth potential |
| Feasibility | ×2 | Can you execute this with current resources and capabilities? |
| Speed | ×1 | Time to results |
| Risk | ×2 | Downside protection (5=safe, 1=catastrophic) |
| Optionality | ×2 | Opens future moves or locks you in? |
| Evidence | ×2 | Supported by current market data and research? |
| Strategic Fit | ×2 | Builds on existing capabilities, assets, relationships? |

**Scale**: 1-5 (1=very weak, 2=weak, 3=moderate, 4=strong, 5=very strong)

**Composite** = (Impact×3 + Feasibility×2 + Speed×1 + Risk×2 + Optionality×2 + Evidence×2 + Strategic Fit×2) / 14

**Minimum threshold**: Any score of 1 on any dimension → automatic flag for elimination or conditional promotion.

**Tier thresholds**: Tier 1 ≥ 3.5 | Tier 2 ≥ 2.75 | Tier 3 = active remainder
```

## results.tsv (header only)

```
iteration	mode	research_topic	options_active	options_eliminated	top_option	top_score	top_score_prev	reviewer_verdict	key_insight
```
