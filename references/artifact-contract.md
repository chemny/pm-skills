# 文件契约

九职责不是九份必交报告。八类一级是逻辑责任，十九项二级按复杂度、独立维护或协作需要拆分。文档路径相对docs，evidence路径相对项目根；无适用内容不生成空文件。文件名小写连字符、不重复项目名前缀；版本在元信息。

| 路径 | 最低责任 |
|---|---|
| project.md | 目标／非目标、基线、约束、未知、当前工作项与有效资料索引 |
| requirements.md | 需求ID、行为／规则、适用质量要求、唯一验收预期与委派索引 |
| product-design.md | 使用方式、关键流程／状态、呈现、决定与限制 |
| architecture.md | 模块结构、选择、接口／数据概要、可行性、风险与实施边界 |
| implementation-plan.md | 任务ID、输入、依赖、范围、验证、集成、DoD与执行条件 |
| verification-report.md | 对象、范围、环境、真实结果、证据、失败／未执行和限制 |
| handover.md | 实际版本／取得方式、使用／启动／安装、配置、限制与接续 |
| operations.md | 按需：检查、告警响应、故障／恢复、依赖维护和反馈 |
| research/questions.md | 研究问题、范围、关键未知、方法和停止条件 |
| research/findings.md | 来源日期、观察、结论、反证、局限和决定影响 |
| specs/requirements/features.md | 功能输入、处理、输出、异常及需求ID |
| specs/requirements/business-rules.md | 条件、优先级、分支、业务状态和允许／拒绝结果 |
| specs/requirements/data-requirements.md | 业务数据含义、来源、用途、敏感性与生命周期 |
| specs/experience/user-flows.md | 用户入口到结果、取消、失败和恢复路径 |
| specs/experience/states.md | 交互状态、触发、反馈、转移与退出 |
| specs/experience/visual-system.md | 按需：字体、颜色、尺寸、间距、组件变体、适配、可访问性 |
| specs/experience/examples.md | 任务／请求、预期交互和输出样例，标明模拟边界 |
| specs/technical/modules.md | 模块职责、内部处理、依赖、错误传播 |
| specs/technical/interfaces.md | 输入输出、校验、鉴权、错误、适用幂等／重试／兼容 |
| specs/technical/data-model.md | 物理字段、类型、关系、约束、一致性、索引、适用迁移 |
| specs/technical/security.md | 角色／资源／操作、执行点、信任边界、数据保护与失败默认 |
| specs/technical/performance.md | 适用规模、延迟／吞吐预算、瓶颈假设、措施，实测另列 |
| specs/technical/deployment.md | 环境、运行组件、配置来源、交付／发布／恢复设计 |
| validation/test-plan.md | 范围、风险、层级、环境／数据、人工自动化和退出条件 |
| validation/test-cases.md | 用例ID、前置、数据、动作、预期、通过标准及代码引用 |
| validation/coverage.md | 需求／规则／状态→方法／实际测试→当前适用证据 |
| validation/experiments.md | 问题、环境／样本、方法、预先通过条件；实际结果引用evidence |
| records/state.yaml | 唯一结构化事实入口；有效输入、任务状态、阻塞、决定／证据引用 |
| records/decisions.md | 决定ID、对象／范围、依据、决定者／来源、修订关系；权限分开 |
| records/issues.md | 实际／预期、复现、影响、修复对象与复验 |
| records/baselines/<id>/manifest | 可取得快照／修订、范围和哈希；不覆盖历史 |
| evidence/<run>/manifest.yaml | 对象、环境、方法／类型、结果和原始输出索引 |
| evidence/<run>/outputs/ | 最少必要实际输出；访问／脱敏／保留约束；不含凭证 |
| specs/experience/prototypes/ | 按需可操作样例；不是生产运行或技术可行性的替代证明 |

## 唯一来源与状态

project登记目标/约束和有效资料入口；requirements掌握权威验收预期，可明确委派详细行为到features/business-rules。coverage引用预期，不改预期；architecture解释实际机器规格并引用OpenAPI、schema、迁移和测试，而非另抄矛盾定义。反推现有代码只能说明实现现状，不能洗成批准要求。

implementation-plan定义任务ID、输入、依赖、范围、验证、集成与DoD；state记录实际状态、阻塞、决定和证据。看板从state派生，不维护产品Tasks与工程Tasks双账，也不另立progress.md。verification-report汇总真实证据；handover提供实际可用版本和接续；operations确需持续运行时独立维护。

独立文档含项目、工作项、范围、draft/in-review/approved/superseded、修订、输入与关联材料。approved只指相应审阅对象，不代表测试通过或发布许可。批准输入保存可取得快照/修订和哈希；新草案不能顶替有效基线，历史不可覆盖。对象或适用配置变化需判定证据失效范围。

证据包含run ID、对象版本/哈希、环境/模型等适用配置、实际方法/入口、类型、结果与原始输出索引；静态/模拟/原型/真实运行分开。缺输出、失败和未执行不能写通过；敏感值不得进入普通日志。脚本只验证形式一致性，不证明用户批准真假或实际产品质量。

旧Overview/MRD/PRD/Design/Tasks及documentation标准只作历史职责来源，不是另一套当前文件标准。不批量移动用户项目或历史证据。生成副本只有母版，专业方法不能覆盖本契约。

## 必交责任与按需拆分的区别

新项目最低交付与时点按[new-project-gates](new-project-gates.md) A01—A10执行。requirements承担PRD责任；有界面新产品核心流程原型为默认必交，无界面用调用/输出样例。合并文档须定位章节及有效版本，不能省必需内容；原型豁免须有替代、风险和用户明确认可。新项目不得以小任务例外跳过产品交接。
