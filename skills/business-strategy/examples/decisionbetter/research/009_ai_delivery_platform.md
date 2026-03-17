# Research: Iteration 009 — AI-Delivered Training as Strategic Bet
*Date: March 2026*

---

## Research Hypothesis

I am researching AI-delivered training as a long-term strategic bet because the owner stated: "in the future AI itself can run tailored training courses and setup." I need to validate whether this is technically feasible, what the market looks like, and how DecisionBetter could build toward this vision.

---

## 1. State of AI-Delivered Training (2026)

**Key finding: This is an emerging market with early proven models (Hard data + Informed opinion)**

From research:
- **Arist** (corporate training platform) has launched an "AI Performance Consultant" that interviews operational staff, identifies problems, and builds training content autonomously. This is described as "the first big step toward autonomous corporate learning." [Informed opinion — Inside Higher Ed, Feb 2026]
- **Agentic AI in education**: Agentic AI can now complete entire online courses autonomously. The question is how to redirect this capability toward teaching rather than completion. [Informed opinion — InsideHigherEd, Feb 2026]
- The AI in education/training market is projected to grow from $7.05B (2025) to $32.27B by 2030 (CAGR ~35%). [Hard data — market research firms]
- **40% of enterprise applications will embed task-specific AI agents by end of 2026.** [Informed opinion — Salesmate AI trends]

**What this means for DecisionBetter**: AI-delivered training is technically feasible today in limited forms. The question is whether it can deliver the outcome that DecisionBetter's workshops deliver: customized, real-workflow implementation with measurable outcomes. Current technology can handle:
- Content delivery (explanations, demonstrations)
- Knowledge assessment (quizzes, prompts)
- Guided exercises with feedback loops
- Workflow documentation and recommendation

It CANNOT yet handle:
- Real-time implementation in a live business system without human oversight
- Facilitation of group dynamics and resistance management
- Trust-building for skeptical clients in Segment 4

---

## 2. What AI-Delivered Training Could Look Like for DecisionBetter

### Phase 2 (12-24 months): Hybrid AI-Assisted Delivery
- **Pre-workshop**: AI conducts the workflow audit and diagnostic (replacing Shane's intake call)
- **During workshop**: AI demonstrates tool use and generates custom examples; Shane facilitates human elements
- **Post-workshop**: AI monitors implementation, sends reminders, provides "coaching" responses via Claude
- **Support**: AI handles tier-1 support questions ("how do I use this prompt template?" "what should I automate next?")
- **Scales**: Shane can handle 2x more clients with AI handling pre/post; he focuses on the human facilitation only

**Tools required**: Claude API (conversational coaching), Claude Code (workflow building), Agent SDK (autonomous post-workshop support), custom intake agent (replaces diagnostic form + call)

---

### Phase 3 (24+ months): Substantially AI-Delivered Programmes
- **AI Workshop Mode**: Client books a product. An AI agent conducts the initial discovery call, maps workflows, identifies top 3 AI opportunities, and generates a custom training curriculum specific to their business.
- **AI Delivery**: The curriculum is delivered as an interactive, conversational program (Claude-powered) with guided exercises on the client's actual tools. Client can run this at their own pace.
- **Human Check-in**: Shane reviews AI-generated roadmaps and checks in at week 2 and completion (1-2 hours total per client instead of 3-8 hours)
- **Revenue model**: Monthly subscription per company ($500-$1,500/month) rather than one-off workshop fees — recurring revenue at scale

**Competitive moat**: Every program is customized to the client's actual workflows using their real data (the DecisionBetter differentiator), but this customization is now AI-driven rather than Shane-driven. The moat is the IP in the curriculum architecture, the diagnostic agent, and the proven methodology — not Shane's personal time.

---

## 3. Why This Vision Requires Productization NOW

**Critical dependency**: AI-delivered training requires:
1. A standardized curriculum architecture (cannot AI-deliver bespoke consulting)
2. Documented methodology with clear stages and outcomes
3. Proven content that generates measurable results
4. A data set of "what worked" from human-delivered workshops

Every workshop Shane delivers today is:
- Validating the curriculum structure
- Building the evidence base for what outcomes are achievable
- Refining the workflow diagnostic methodology
- Creating the training data for the AI delivery system

**This is why productization (iteration 005-007) is the prerequisite for the AI delivery vision, not just a near-term tactic.** If Shane keeps delivering bespoke workshops with no standardization, there is no curriculum to AI-deliver.

---

## 4. The Anthropic Stack Advantage

Shane prefers Claude Code + Anthropic stack. This is not just a technology preference — it is a strategic advantage for this specific vision:

- **Claude API**: Powers the conversational coaching and diagnostic agent (the AI "facilitator")
- **Claude Code**: Powers the workflow automation building component (DFY embedded in the AI-delivered program)
- **Anthropic Agent SDK**: Powers the multi-step autonomous learning journeys
- **Claude Partner Network**: Provides Anthropic support, co-marketing, and technical resources for exactly this use case

The Anthropic stack is better positioned for this vision than n8n/Make.com because the vision is NOT "automation workflow builder" — it is "conversational AI training and implementation." Claude is purpose-built for this.

---

## 5. Market Opportunity at Phase 3

**Bottom-up TAM for AI-delivered program (Phase 3 vision)**

If DecisionBetter reaches Phase 3 with a subscription-based AI-delivered training product:

- Target: AU SMBs with 10-100 employees already using AI tools but not systematically
- Addressable AU market: ~50,000 businesses in this profile
- Subscription price: $500-$1,500/month per company
- At 0.1% penetration: 50 clients × $750 avg = **$37,500 MRR ($450K ARR)**
- At 0.5% penetration: 250 clients × $750 avg = **$187,500 MRR ($2.25M ARR)**
- This is a fundamentally different business than the workshop model — recurring, scalable, not founder-time-dependent

**Comparison to current model ceiling**:
- Current model maximum (solo): ~$200K-$250K ARR (12 DFY + workshops)
- Phase 3 AI-delivery potential: $450K-$2.25M ARR with same team

---

## 6. Risk Assessment for Phase 3

| Risk | Severity | Mitigation |
|---|---|---|
| Technology not mature enough | Medium | Phase 2 hybrid model bridges the gap; don't attempt full automation before Phase 2 is proven |
| Clients won't trust AI-delivered training | High | Phase 2 (human + AI) builds trust before Phase 3; outcome guarantee remains in Phase 3 |
| Competitors (Google, Microsoft) build similar products | High | DecisionBetter's moat is AU SMB customization + workflow specificity, not generic AI training |
| Shane doesn't have time to build the platform while delivering workshops | High | The platform is built incrementally from each workshop's documented methodology; not a separate project |
| SMBs won't pay subscription for training | Medium | Evidence: LinkedIn Learning, Coursera for Business growing at 20-30%/year; subscription model validated |

---

## Sources

- [Agentic AI in Education 2026](https://8allocate.com/blog/agentic-ai-in-education-use-cases-trends-and-implementation-playbook/)
- [Agentic AI Can Complete Whole Courses](https://www.insidehighered.com/news/tech-innovation/artificial-intelligence/2026/02/26/agentic-ai-can-complete-whole-courses-now)
- [AI Agent Trends 2026](https://www.salesmate.io/blog/future-of-ai-agents/)
- [Josh Bersin — Corporate Training to Enablement](https://joshbersin.com/2026/03/the-world-of-corporate-training-lurches-toward-enablement/)
- [Anthropic Claude Partner Network](https://www.anthropic.com/news/claude-partner-network)
