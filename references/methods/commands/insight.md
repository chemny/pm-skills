---
description: Run demand insight (需求洞察) — synthesize market signals, concrete user behavior, counterevidence and domain-informed analysis into bounded conclusions for the skill user's product decision. New products may pass for prototype exploration without first-hand validation.
argument-hint: "<need / market-analysis conclusion / product idea>"
uses: [opportunity-solution-tree]
outputs: ["趋势与行为洞察+适用人群+产品取舍+待验证项"]
---

> **Capability loading:** For each capability named in `uses`, use its visible Skill when present; otherwise read `../../capabilities/<name>.md` completely before applying it.

# /insight -- 需求洞察 (Demand Insight)

Optional insight method; not a mandatory second lifecycle stage. It answers: **what is changing, for whom, why it matters, and which product decision that judgment supports?** Input: the market-analysis conclusion (or a raw idea). Output: evidence-linked conclusions and their decision boundary; research tasks are subordinate.

> **Two distinct decisions, not one universal evidence bar.** For a new product, convergent trend signals, relevant cases, counterevidence and an explicit inference chain may establish **“趋势推演成立，可进入原型探索”** even when no one has used the proposed product. That is NOT **“目标需求得到验证”**, willingness to pay, or approval for major development spend. For an existing product, direct logs, support cases and observed behavior may support stronger user-need conclusions. Judge evidence relative to the specific claim and investment decision, not by a fixed requirement for interviews. If only loose E4/U speculation remains, label “探索假设（待一手验证）”, not completed insight.

> **Collaborate + don't block (CONVENTIONS 当前决定边界).** Confirm core framing (the need statement, the target) **with the user**, don't autopilot. Grade evidence honestly and flag what's unvalidated, but **if the user has decided to proceed, help them — surface risks, never refuse or stall the pipeline.** The decision is theirs.
> **Do your OWN research — don't just expand ①.** Inheriting ①'s persona ≠ skipping fresh fact-checking. This stage must run its own searches for need evidence and leading indicators, triangulate across source classes, check contrary signals, and loop back to fill gaps (CONVENTIONS §4/§8). Expanding the upstream report without new verification is a fail.
> **Follow [`CONVENTIONS.md`](../../CONVENTIONS.md)** for all cross-cutting discipline (how to ask, plain language, depth, honesty, methodology-backstage, red-team). This command adds only the **insight-specific** logic.
> **Research gate (mandatory):** Read and execute [`Deep Research Contract`](../../contracts/deep-research-contract.md) at `standard` or `full` intensity. This stage needs its own incremental ledger and fresh need-evidence searches; inheriting ① never counts as a passed research gate by itself.
> **Decision handoff:** Insight must conclude which **bounded need/opportunity thesis** and candidate user behavior should be taken into strategy, at what evidence strength and investment scope. Offer a reasoned recommendation and alternatives if more than one candidate remains; the user chooses. If a missing choice changes the strategy's starting target, ask now rather than writing “待定” and passing it forward. Follow the [`产品交付物契约`](../../contracts/product-artifacts.md); do not claim a new product's demand is validated when only trend evidence exists.

## Step 1 — Frame the decision and accountability
- Record the exact decision this stage must support: explore a prototype, choose a segment, approve a scoped PRD, or commit major resources. Evidence sufficient for one may be insufficient for another.
- Carry out the analysis to a domain-expert standard: use relevant industry knowledge, concrete cases, data, counterexamples and explicit reasoning; research unfamiliar details instead of inventing experience. **使用者审核** the output, corrects what is unsuitable, and is responsible for the final judgment and approval. Do not introduce a separate expert-review gate or claim that the AI has personal industry experience.
- Inherit the user's approved product definition; do not silently narrow the product, geography, platform or business model.

## Step 2 — Frame the real job (JTBD)
- The functional job + the emotional/social job. Not the feature — the job.
- State it: *"When ___ (situation/trigger), I want to ___ (motivation), so I can ___ (outcome)."*
- Capture the current workaround and the **struggling moment** (when/why it hurts today).
- Optionally apply the **opportunity-solution-tree** skill to connect the job to the outcome.

## Step 3 — Segment path: inherit if available, intake if standalone
Preferred path: inherit the data-grounded **user persona, typical scenarios, buyer/willingness-to-pay, and viable target segment** from `/market-analysis` (①). **Insight consumes them — it does not re-invent who the user is.**

Standalone path (§0d): if ① is missing, do **not** stop by default. Enter a short intake and ask only the Class A fields needed for this stage:
- target user / segment;
- concrete usage situation;
- geography;
- commercial direction / who may pay.

Then proceed with a clear caveat: **"缺少上游市场分析；本次趋势或人群判断须单独标明依据和边界。"** Any segment or scenario from the user is treated as user-provided input, not validated market fact. If the user cannot provide these fields, ask and wait; do not fabricate.

If you have ①, **restate the inherited segment + scenario in one line** as the basis, then drill into the specific need below. Optional refinements must be **sourced**, not invented, and flagged as a refinement of ①'s finding.

If ① only identified broad candidate segments, say **尚未确认滩头人群** and compare candidates as research hypotheses. Do not promote one role, language, OS or workflow to an approved target without the user's decision.

A fabricated persona/scenario, or silently "discovering" the user from scratch while pretending it came from ①, is a fail.

## Step 4 — Synthesize actual insight, not a list of unknowns
For each decisive conclusion, write **concrete case/data → repeated pattern or leading signal → mechanism and alternative explanation → bounded market or behavior judgment → downstream product action**. Cite original sources, dates, audience and denominator where applicable. Separate observed fact from expert inference, and show the strongest counterexample. A trend forecast can be useful without direct data for the proposed product, but cannot be presented as observed adoption.

- Map behavioral segments by **task, trigger, frequency, environment, existing workaround, decision maker and constraints**. Use a real evidence-based behavioral portrait; if data are thin, label candidate segments rather than inventing named personas or demographic details.
- For need viability, grade the four questions (pain/workaround, frequency, nameable segment, switching/payment) as **supported / contradicted / unresolved**, each with evidence type and scope. Do not score all four "failed" just because a new product has no users; likewise, competitor supply alone cannot prove buyer demand.
- Make the forecast falsifiable: specify which observed change would strengthen or overturn it. Keep a separate **“目标需求得到验证”** status for direct evidence from relevant users, existing-product behavior, or actual experiments.

## Step 5 — Identify the decisive uncertainty
- Name the single belief that would most change the next investment decision if false. Rank other assumptions by consequence and cheapness of learning; do not let the assumptions list become the main deliverable.
- Apply **identify-assumptions-new/existing** + **prioritize-assumptions** only when those methods improve the decision.

## Step 6 — Decide the permitted next step and only the necessary validation
- **趋势推演成立**: if sources converge and reasoning survives counterevidence, the user may approve bounded prototype exploration or a scoped PRD; carry low/medium confidence and explicit tests downstream. This is not a promise of conversion or product-market fit.
- **目标需求得到验证**: only assert this for the specific segment, task and geography supported by direct behavior, usage or experiment evidence. It may support stronger scope or investment, still subject to product and technical decisions.
- **推演未成立 / 关键事实仍未知**: report the unsupported claim and the smallest research or prototype test that could resolve the decision. User may choose to proceed with acknowledged risk; do not fabricate a pass or unilaterally veto the project.
- **访谈提纲按需生成**: interviews are one possible method, not a mandatory artifact. Use past concrete behavior if interviewing; product logs, observation, competitor task comparison or prototype tests may be more appropriate. Propose measures and stop/continue conditions proportional to the decision; do not invent universal sample sizes or success thresholds.

## Output (methodology backstage, plain headings — CONVENTIONS §7)
将观察、趋势、需求判断、反证和局限写入docs/research/findings.md，按有效输入和范围维护；用户产品选择单独记records/decisions.md，需求引用适用结论。研究证据等级不是整个项目阶段批准，旧MRD仅作历史。单项交付不扩全流程。
```
# 需求洞察：[主题]
日期 · 输入来源

## 本次判断与适用范围                清楚回答什么变化值得关注、什么尚未成立
## 关键洞察                          每条有真实信号、机制、反证、趋势/行为判断和产品动作
## 人群与行为                        证据支持的场景/工作习惯；未确认滩头人群时只列候选
## 产品取舍                          对策略、PRD、原型的输入与禁止升级的推断
## 本阶段决定与交接                  使用者接受的优先命题／候选行为、适用范围、反证与策略可直接继承的固定输入
## 关键待验证项                      只列会改变当前或下一项决定的验证任务
## 研究与审阅状态                    Research Gate、来源边界、使用者审核与决策状态
```

## Next Steps
- "趋势推演通过且用户选择继续？→ 带着不确定性做小范围原型、策略或有明确实验边界的 PRD；不要把原型许可解释为重投入许可。"
- "关键推演未成立？→ 先补最小的承重证据或让用户决定是否带风险推进。"

## Notes
- The deliverable is a **defensible judgment that changes a product decision**, not a long validation plan. Honesty includes stating a bounded positive forecast when the evidence supports it.
- If the input is a market-analysis "PIVOT", run insight on the *pivoted* need, not the rejected one.
