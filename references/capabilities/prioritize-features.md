---
name: prioritize-features
description: "Prioritize a backlog of feature ideas based on impact, effort, risk, and strategic alignment with top 5 recommendations. Use when prioritizing a feature backlog, making scope decisions, or ranking product ideas."
scenarios: ["这堆功能我该先做哪个", "帮我把backlog排个优先级", "按影响和成本给功能排序"]
---

> 当前仅作按需专业方法；先遵循[文件契约](../artifact-contract.md)。不将旧格式、数量或人类团队假设变为通用门槛，不把方法结果当用户批准或运行事实。


## Prioritize Feature Backlog

Evaluate and rank a backlog of feature ideas to identify the top 5 to pursue.

### Context

You are helping prioritize features for **$ARGUMENTS**.

If the user provides files (spreadsheets, backlogs, opportunity assessments), read and analyze them directly.

### Domain Context

For framework selection guidance, see the `prioritization-frameworks` skill. Key recommendations:

**Opportunity Score** (Dan Olsen, *The Lean Product Playbook*) is recommended for evaluating customer problems: Opportunity Score = Importance × (1 − Satisfaction), normalized to 0–1. High Importance + low Satisfaction = best opportunities. Prioritize **problems (opportunities)**, not solutions.

**ICE** is recommended for quick scoring of initiatives: Impact (Opportunity Score × # Customers) × Confidence × Ease. **RICE** adds Reach as a separate factor for larger teams.

### Instructions

The user will describe their product objective, desired outcomes, and provide feature ideas. Work through these steps:

1. **Understand priorities**: Confirm the product objective and success metrics.

2. **Evaluate each feature** against:
   - **Impact**: How much does it move the needle on desired outcomes? Consider Opportunity Score if customer data is available.
   - **Effort**: How much development, design, and coordination is required?
   - **Risk**: How much uncertainty exists? What assumptions need testing?
   - **Strategic alignment**: How well does it fit the product vision and current goals?

3. **Recommend the top 5 features** with:
   - Clear ranking (1-5)
   - Brief rationale for each selection
   - Key trade-offs considered
   - What was deprioritized and why

4. **Present as a prioritization table** if helpful.

Think step by step. Save as markdown if the output is substantial.