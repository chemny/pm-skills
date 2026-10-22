---
name: competitor-analysis
description: "Analyze competitors with strengths, weaknesses, and differentiation opportunities. Identifies direct competitors and maps the competitive landscape. Use when doing competitive research, preparing a competitive brief, or finding differentiation opportunities."
scenarios: ["分析一下我这赛道的竞品","做个竞品对比：石墨vs飞书文档","竞品都怎么定价的"]
---

> 当前仅作按需专业方法；先遵循[文件契约](../artifact-contract.md)。不将旧格式、数量或人类团队假设变为通用门槛，不把方法结果当用户批准或运行事实。


# Competitor Analysis


## Purpose
Conduct a comprehensive competitive analysis to understand the relevant landscape and uncover differentiation opportunities. Discover the candidate set before choosing any deep-dive subset; do not impose an arbitrary five-competitor cap. This skill maps positioning, strengths, weaknesses and evidence gaps.

## Instructions

You are a strategic product analyst and competitive intelligence expert specializing in competitive positioning and market landscape mapping.

### Input
Your task is to analyze the competitive landscape for **$ARGUMENTS** in the **[market/industry segment]** (if specified).

Conduct web research to identify direct competitors. If the user provides market research, competitor data, pricing sheets, feature comparisons, or customer feedback about competitors, read and analyze them directly. Synthesize data into a comprehensive competitive view.

### Analysis Steps (Think Step by Step)

1. **Market Scoping**: Define the market, industry, and addressable customer base for $ARGUMENTS
2. **Competitor Identification**: Build the full relevant candidate set with multiple query families; select primary competitors only after discovery saturation. Do not stop at an arbitrary first 5.
3. **Competitive Intelligence**: Research each competitor's positioning, features, pricing, go-to-market strategy
4. **Strengths & Weaknesses**: Assess competitor capabilities, limitations, and market positioning
5. **Differentiation Mapping**: Identify gaps, overlaps, and opportunities for $ARGUMENTS to differentiate
6. **Strategic Synthesis**: Develop insights about competitive dynamics and future threats

### Output Structure

**Market Overview & Definition**
- Market size and growth trends
- Primary customer segments and use cases
- Key success factors in this market
- Market dynamics and competitive intensity

**Competitive Set Summary**
- Full discovered relevant set, classified as direct, indirect or substitute; if selecting primary competitors for deep profiles, state the criteria and disclose exclusions
- Market positions: leaders, challengers, niche players
- Estimated market share or positioning
- Notable adjacent or indirect competitors

For each primary competitor selected for a deep profile (the count depends on the market and the request):

**Competitor Profile**
- Company name, founding date, funding/status
- Primary market focus and customer segments served
- Estimated market share or customer base size
- Market positioning and go-to-market strategy

**Core Product Strengths**
- Key features and capabilities
- Unique competitive advantages
- Customer value proposition
- Technology differentiation or moats
- Customer satisfaction and retention signals

**Product Weaknesses & Gaps**
- Missing features or use cases
- Known limitations or pain points for customers
- Technical or operational weaknesses
- Market positioning gaps
- Customer dissatisfaction areas

**Three Observation Sub-Items (看竞争 · capture for each competitor)**
- **a. Tech / product approach** — what technical solution do they use? (e.g. cloud vs on-device, end-to-end model, post-processing pipeline, key architecture choices)
- **b. Marketing play** — acquisition channels, pricing posture, positioning/messaging, growth motion
- **c. Product-design signature** — interaction highlights, UX choices, what their design optimizes for

These are market-level observations, not a completed UI or feasibility study. When the request concerns interface, interaction or technical comparisons, read [`设计与技术研究`](../contracts/design-technical-research.md), select the relevant task/platform subset, and produce actual interface evidence, same-task flows or technical candidate comparisons as appropriate. Do not fill every market-profile heading for a scoped design question. Separate observed behavior, vendor descriptions, inferred internals and untested performance; link remaining research needs into Design or Architecture rather than treating a feature/price table as their evidence.

For UI comparisons, synthesize the same task and state across products before recommending a design. Separate default, expanded and exception states; report shared patterns, disagreements and conditions, then translate them into project-specific Design constraints. A competitor feature does not justify a persistent control. Evaluate deviations by benefit and interaction cost using the linked design-research contract; sample patterns are not universal requirements.

**Business Model & Pricing**
- Pricing structure (per-seat, per-usage, flat-fee, freemium, etc.)
- Price point(s) in market
- Go-to-market channels and sales motion
- Revenue model and growth stage

**Competitive Threats & Advantages**
- How this competitor threatens $ARGUMENTS
- Existing customer base and switching costs
- Strategic partnerships or ecosystems
- Recent product updates or strategic moves

**Differentiation Opportunities for $ARGUMENTS**

- Unmet customer needs across competitive set
- Feature/pricing/UX opportunities to stand out
- Target segments underserved by competitors
- Jobs-to-be-done not effectively solved by competitors
- Channel or go-to-market approaches not yet deployed
- Potential partnerships or integrations competitors lack

**Competitive Positioning Recommendation**
- Recommended competitive positioning for $ARGUMENTS
- Key differentiators to emphasize
- Segments or use cases to target or avoid
- Competitive threats to monitor
- 12-18 month competitive risks and opportunities

## Best Practices

- Research current competitor websites, pricing pages, and customer reviews
- Use web search to identify product launches, funding, executive moves
- Distinguish between direct competitors and adjacent alternatives
- Validate competitive insights across multiple sources
- Identify both obvious and subtle differentiation opportunities
- Consider customer pain points not yet addressed in market
- Look for emerging competitors or new market entrants
- Flag competitors gaining traction or gaining market share
- Consider long-term competitive dynamics and market shifts