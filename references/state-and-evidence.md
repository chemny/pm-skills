# 状态、就绪与证据接口 v1

state-schema.json为交换结构；runtime.py实现跨引用、依赖、状态及对象检查，不声称仅JSON Schema能验证全部语义。JSON语法是合法YAML，默认无第三方依赖；通用YAML输入需要环境已有PyYAML，缺少时准确报错，不自动安装。解析拒绝重复键。

state有schema_version=1、project/work_item非空、inputs/decisions/open_decisions/tasks数组。input含id/path/sha256/status=approved，path为项目根内可取得的有效快照。task含id/status/input_ids/decision_ids/depends_on/conditions/evidence_refs/required_evidence_kinds/object。未启动任务可以暂缺条件但不会ready；ready/running/verifying/done声明须有真实依据。

conditions有inputs、decisions、design、dependencies、environment、tools、authority、verification八项。适用时applicable=true、satisfied=true并有basis；不适用须applicable=false及reason，不是把未知写成不适用。检查器只核这些字段和实际引用，不能证实人类批准真假、设计质量或真实工具权限；主Agent必须核依据语义。依赖须真实done且其证据有效，不能从一个乐观状态字段放行。

决定含id/status，pending或needs-recheck必须出现在open_decisions；approved须selected和approval_ref。pending不自动阻断无关任务。done须object与适用的通过证据及required_evidence_kinds；取消不是成功依赖。状态转换使用runtime.transition并给理由，保留history；done重开回planned或blocked，不覆盖历史运行。

## 实际CLI

```text
python3 scripts/check_state.py PROJECT_ROOT docs/records/state.yaml
python3 scripts/check_artifact_refs.py PROJECT_ROOT docs/records/state.yaml
python3 scripts/check_artifact_refs.py PROJECT_ROOT --manifest evidence/RUN/manifest.yaml
python3 scripts/record_evidence.py PROJECT_ROOT request.json
```

检查器不写文件：0=形式有效（planned仍可能阻塞，须读ready_tasks/blocked_tasks），1=一致性错误，2=输入/引用/调用错误。记录器0=被执行命令成功，1=失败/阻塞，2=请求/写入错误。**退出0不等于产品通过或操作授权。**

record_evidence是真实命令执行辅助器。request含run_id、object.files（相对路径→sha256，可另含configuration）、environment、method、kind（static/simulated/prototype/runtime/review）、command（非空argv数组，不用shell）、可选output_paths和timeout_seconds。调用者必须先核操作授权；读取一个请求文件不等于可以执行里面任意命令。run_id单批唯一；命令返回码/超时决定原始结果，不能由用户传passed覆盖。

先在受管.pending-RUN记录启动/完成journal，再原子完成evidence/RUN。命令改变所声明对象、缺输出、敏感输出或写入失败时保留pending以便核实际副作用；不要删journal并直接重跑。已有批次请求相同且证据有效时幂等返回；不同请求拒绝覆盖。路径不能越出项目根；只输出最少必要内容。敏感模式检测是有限的拒收辅助，不能保证全量脱敏；不确定先人工处理，禁止把凭证放入普通证据。

manifest有schema_version、run_id、object、environment、method、kind、result、outputs（path/sha256），实际执行还记录命令/退出/时间。对象的源码与适用配置都是身份；旧对象或被改写的输出不能支持当前完成。static/simulated/prototype不能替代任务要求的runtime证据。记录器证明命令运行与索引，不理解产品断言；通过仍需用例与人工评审。

计划定义任务，state唯一记录实际事实；看板派生。不因为文件主路径更新就替换批准快照。恢复先核工作区、journal、实际成果和副作用，再修状态。格式可读不等于语义已核。


## v2：具体任务开工与受管执行

v1仅兼容读取/核历史，不自动迁移或取得新执行许可。check_state区分结构valid、legacy候选与execution_ready_tasks；实施看具体check_task_ready的can_start，不从valid/退出0推断开工。v2保留原八项条件和任务/决定/证据，增加以下可核引用（路径均相对项目根）：

- context：entry=new/change/bug/single、interface=ui/cli/api/service/skill、mode=discussion/planning/execution、paused布尔、scope、本次authority={path,sha256}。新项目拆小不能改entry；暂停须真实答复明确恢复才撤销。
- artifacts：{id,kind,path,sha256,scope,review_ref,section?}。kind可为project/requirements/experience/prototype/examples/architecture/plan/validation。合并同路径时section必须定位实际章节。占位或过期哈希拒绝。
- reviews：{id,kind,actor,status,scope,source:{path,sha256},objects:{artifact_id:sha256}}。工程内容审阅和用户产品认可分别管理；product需actor=user并覆盖本轮requirements/experience/prototype或examples。ui替代原型需waiver记录reason/risk/alternative、真实用户来源及替代样例。记录不是签名认证，主Agent必须核原话和内容。
- task：activity=documentation/research/prototype/experiment/implementation/test/delivery、scope、artifact_refs、write_paths、commands（确切argv数组的列表）、max_attempts、timeout_seconds；new implementation需有效project/requirements/experience/architecture/plan/validation及适用prototype/examples与product_review_ref；change/bug可用baseline_refs引用有效相关基线。
- experiment字段：problem/necessity/method/sample/expected/pass_criteria/fail_criteria/stop/data_scope/return_to_product、max_attempts、timeout_seconds、authorization_id、effects。授权决定需kind=experiment、scope和source引用、selected/approval_ref；effects的capture/upload/install/pay/permissions/configuration须明确布尔。true时另有effect_refs指向同scope、kind=operation、operation匹配、真实来源且列入decision_ids的具体许可；未知不得写false。

只读开工命令：
```text
python3 scripts/check_task_ready.py ROOT docs/records/state.yaml TASK_ID [REQUEST_REL]
```
0=该任务在当前输入下可以启动；1=阻塞；2=调用错误。输出can_start、blocked_reasons、state_digest，不发放可长期复用的许可。写入或调用前重查，输入/设计/许可变化后失效。

record_evidence请求原字段保留，新增必填state_path、task_id，command必须逐项匹配task.commands且timeout不超任务上限。public runtime.record同样受管；_record_command只是低层内部原语，不是许可入口，不得以直接import它绕过。先查就绪、再锁内重核，记录合法ready/running和运行预约，再执行、保存真实原始输出，核当前对象、范围及有效输入，返回后由主Agent完成verifying/done和验收判定。

runs记录每次尝试；失败也耗额度；同请求同run的有效证据可只读幂等返回，不重复执行。超次数、未知任务、命令不符、暂停或旧状态拒绝。实际改动越write_paths、执行中有效规格失效或控制state被改时，不因退出0判成功；控制state变化保留实际内容，不能覆盖用户暂停。异常保留pending和预约，接续先核实际副作用。

直接宿主工具仍须有本轮具体任务开工检查、范围绑定、实际轨迹与改动核对；缺少这些不是“另一个合法入口”。snapshot_files/audit_changes可比较项目内文件，未登记源码/执行与台账矛盾时，先阻断受影响任务并报告，不替用户静默清理。它们不观察全部网络/外部系统，也不构成宿主硬权限隔离。

源文件示例与字段测试见tests/test_project_gates.py；模板保持draft，不预填真实批准。单进程实验也须使用有效v2状态并在同进程核具体任务与合法转换；不能为了少启动进程而绕过准入。

## 执行后的完成接口与历史补录

`record_evidence`/`runtime.record`直接保存进程stdout/stderr，输出索引标明process-stdout、process-stderr或copied-artifact；任务runs关联run_id、state_digest、实际结果和evidence_ref。整理、脱敏或重建的摘要另存并标类型，不冒充原始捕获。读历史文件不能声称本轮执行。

人工核实实际断言及限制后，用以下接口绑定同一对象的证据并完成状态转换；它只复用已有证据，不运行命令：

```text
python3 scripts/complete_task.py ROOT STATE_REL TASK_ID "实际核验理由" MANIFEST_REL [MANIFEST_REL ...]
```

v2 experiment，以及要求runtime证据的implementation/test，按具体执行渠道核对当前任务、对象、登记尝试及前置state_digest；范围、控制状态和后置检查通过。证据渠道不改变任务准入、用户暂停和真实操作许可。直接transition到done也须先核当前状态及完成证据；完成失败不写入半完成状态。检查器不理解业务语义，不认证人类授权，也不观察所有宿主工具或外部副作用。

### 本轮四项修正的边界

1. **按渠道取证**：`provenance=managed-command`继续要求允许的确切command及本次run的stdout/stderr。其他宿主工具可用`provenance=task-bound-host-tool`：task预先列`tool_calls`（完整tool及arguments对象）；manifest含完全匹配的tool_call、receipt={tool,call_id}、execution_result与assertion_result=passed，以及role=tool-response的真实响应文件及哈希。preflight另含state_ref={path,sha256}，指向实际执行前保存的状态快照；检查器复核其就绪、摘要、调用范围和次数，runs绑定同一run_id及state_digest。沿用scope_audit、control_state_changed及postflight要求。此处只接纳证据契约，不新建自动调用器；调用标识和响应是否来自真实宿主、外部影响是否符合授权，仍须主Agent核验。手工虚构回执不是合法入口。UI、远程CI等用其真实响应/操作结果导出，不伪造stdout/stderr；尚无可信记录时仍阻塞。
2. **预期失败**：本地命令默认退出0。负向用例须在执行前写入task.command_expectations数组，每项含确切command、预期非零returncode（1—255）及非空stdout_contains和/或stderr_contains。记录器只采用任务声明，不接受请求临时改判；保存原始execution_result、returncode和实际assertion_result。预期代码与所有声明的输出断言均匹配，且范围/准入检查通过，才可判该用例passed；超时、无法启动、断言不符不豁免。manifest与runs保存同一预期，完成时重核，不能事后把失败改成预期。用例通过不代表操作成功或产品验收通过。
3. **验收与历史分开**：evidence_refs只列本轮当前对象的验收依据；旧引用在complete_task替换时转存history_evidence_refs，原文件和runs保留。历史失败/中断不要求删除或最近一次必须成功，但每个未通过尝试须在attempt_resolutions中按run_id记录status=resolved/superseded/not-applicable、具体reason及指向当前验收依据的非空evidence_refs；未处置的相关问题仍阻塞。解释是否充分、对象与用例是否覆盖实际问题仍需人工核验，不能用“已处理”空话替代复验。
4. **旧完成状态兼容**：本轮完成校验标识为task.completion_policy=2；新开始的受管运行和任何新done转换自动使用此规则。已有done且没有标识或标识为1时，不追溯施加本轮新增完成检查，也不改状态；evaluate在historical_completion_not_rechecked中明确列出，不能将其称为本轮已复核。原有对象/哈希/授权引用检查仍有效。确需复核先说明原因及影响，重开任务保留历史后按当前规则执行；不自动迁移、不自动重跑、不借旧状态取得新许可。

对已经发生但未登记的操作，仅做历史补录：保留原文件、真实用户授权线索、实际观察、补录时间、原始日志缺失及准入偏差；标provenance=retrospective-unmanaged，不造state_digest或事前检查。将技术观察与流程合规分开，缺失准入的实验任务保持blocked，另一个获准的记录维护任务可以完成。不得为了补记录重跑操作，或解除原项目暂停。见[recovery](recovery.md)。


## 已有项目的单项任务与唯一活动台账

先定位项目实际使用的活动state及来源；已有合法的自定义路径可以沿用，不强制迁移到默认文件名。单项研究、诊断、交付或复核在该state里新增任务，引用本轮真实输入与授权；记录器state_path仍指向它。不要因新任务属于single、名称不同、scope标签不同或要保留旧任务原样，另建同根活动state来执行。新增任务不等于批准、修改或完成其他任务，原有待决定、暂停和失败均按实际保留，独立就绪任务仍可推进。

基线快照、导出和历史台账须明确只读用途，不用于新任务准入或运行。确需切换当前工作项时在原活动台账中显式保留历史并更新当前上下文；不能偷偷复制为第二份活动账。真正独立的新项目使用其独立根目录和相应授权。若活动台账损坏、不可写或来源冲突，先按恢复规则核事实，只阻断受影响工作，不用另一个state掩盖问题。历史上已经使用副账的动作如实注明原入口与偏差，不能补造从主账执行的事前记录。
