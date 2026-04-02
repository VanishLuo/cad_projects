# License Management Software Executable Development Process (Python GUI)
# License管理软件可执行开发流程（Python GUI）

## 0. Scope and Boundaries
## 0. 范围与边界
- In scope: local license record management, import/export, expiration reminder, search/filter, provider-aware start/stop workflow.
- 范围内：本地license记录管理、导入导出、到期提醒、搜索筛选、按服务商差异化的启停流程。
- Out of scope: modifying original license file content, cloud multi-tenant architecture, online account system.
- 范围外：修改原始license文件内容、云端多租户架构、在线账号系统。
- Definition: add/delete/update means local database record operations only.
- 定义：增删改仅指本地数据库记录操作。

## Global Deliverables and Quality Gates
## 全局交付物与质量门禁
- Required deliverables:
- 必备交付物：
	- Requirements baseline and change log
	- 需求基线与变更记录
	- Architecture and module design docs
	- 架构与模块设计文档
	- Test plan, test report, known issues list
	- 测试计划、测试报告、已知问题清单
	- Packaging script and release notes
	- 打包脚本与发布说明
- Global acceptance gates:
- 全局验收门禁：
	- P0/P1 defects are all closed before release
	- 发布前P0/P1缺陷全部关闭
	- Core use cases pass rate = 100%
	- 核心用例通过率=100%
	- No blocker in installation/startup/import/start-stop/export flow
	- 安装、启动、导入、启停、导出流程无阻塞问题

## Stage Execution Template
## 阶段执行模板
Use the following template in each stage:
每个阶段按以下模板执行：
- Task ID format: T{stage}.{index} (example: T5.3)
- 任务编号格式：T{阶段}.{序号}（示例：T5.3）
- Inputs / 输入
- Tasks / 执行任务
- Outputs / 输出物
- Acceptance Criteria / 验收标准
- Owner / 责任角色
- Duration / 预计工期

---

## 1. Requirements Baseline and Design
## 1. 需求基线与设计

### Inputs / 输入
- Existing requirement document and stakeholder feedback.
- 现有需求文档与干系人反馈。

### Tasks / 执行任务
- [T1.1] Freeze functional scope (CRUD local records, import/export, expiration reminder, search/filter, start-stop, provider comparison).
- [T1.1] 冻结功能范围（本地记录增删查改、导入导出、到期提醒、搜索筛选、启停、服务商比对）。
- [T1.2] Define non-functional targets (stability, performance, security, maintainability).
- [T1.2] 定义非功能目标（稳定性、性能、安全性、可维护性）。
- [T1.3] Produce UI interaction draft (main list, import dialog, provider start/stop panel, compare view).
- [T1.3] 产出UI交互草图（主列表、导入弹窗、服务商启停面板、比对视图）。
- [T1.4] Review and sign off requirement baseline.
- [T1.4] 评审并签署需求基线。

### Outputs / 输出物
- Signed requirement baseline v1.0.
- 签字确认的需求基线v1.0。
- Feature list with priorities (P0/P1/P2).
- 含优先级（P0/P1/P2）的功能清单。
- UI prototype and key interaction flow.
- UI原型与关键交互流程。

### Acceptance Criteria / 验收标准
- Each feature has explicit boundary and success condition.
- 每个功能都有明确边界与成功判定。
- Requirement conflicts are resolved and documented.
- 需求冲突已解决并记录。

### Owner / 责任角色
- Product owner + tech lead.
- 产品负责人 + 技术负责人。

### Duration / 预计工期
- 2-4 working days.
- 2-4个工作日。

---

## 2. Architecture and Technology Selection
## 2. 架构与技术选型

### Inputs / 输入
- Requirement baseline v1.0.
- 需求基线v1.0。

### Tasks / 执行任务
- [T2.1] Select stack: Python 3.12, PyQt5/PySide6, SQLite, openpyxl, paramiko, PyInstaller.
- [T2.1] 选型：Python 3.12、PyQt5/PySide6、SQLite、openpyxl、paramiko、PyInstaller。
- [T2.2] Define layered architecture: UI layer, application service layer, provider adapter layer, repository layer.
- [T2.2] 定义分层架构：UI层、应用服务层、服务商适配层、仓储层。
- [T2.3] Define data model and migration strategy.
- [T2.3] 定义数据模型与迁移策略。
- [T2.4] Define logging and error code rules.
- [T2.4] 定义日志与错误码规范。

### Outputs / 输出物
- Architecture diagram and module responsibilities.
- 架构图与模块职责说明。
- Data schema v1 (tables, indexes, constraints).
- 数据库结构v1（表、索引、约束）。
- Provider adapter interface contract.
- 服务商适配接口契约。

### Acceptance Criteria / 验收标准
- All major scenarios map to concrete modules.
- 所有核心场景都能映射到明确模块。
- New provider can be integrated without modifying core business flow.
- 新增服务商无需修改核心业务流程。

### Owner / 责任角色
- Tech lead.
- 技术负责人。

### Duration / 预计工期
- 2-3 working days.
- 2-3个工作日。

---

## 3. Environment and Project Initialization
## 3. 环境与工程初始化

### Inputs / 输入
- Approved architecture and technology stack.
- 已批准的架构与技术栈。

### Tasks / 执行任务
- [T3.1] Create Python virtual environment and dependency lock file.
- [T3.1] 创建Python虚拟环境与依赖锁定文件。
- [T3.2] Initialize project structure (src/tests/docs/scripts).
- [T3.2] 初始化工程结构（src/tests/docs/scripts）。
- [T3.3] Configure lint, format, and test tools.
- [T3.3] 配置lint、格式化、测试工具。
- [T3.4] Set up CI baseline for static check and tests.
- [T3.4] 建立静态检查与测试的CI基线。

### Outputs / 输出物
- Reproducible development environment guide.
- 可复现的开发环境说明。
- Initial runnable skeleton app.
- 可运行的初始骨架程序。

### Acceptance Criteria / 验收标准
- New machine can run app and tests with setup guide.
- 新机器按文档可运行程序与测试。
- CI passes for baseline checks.
- 基线检查在CI中通过。

### Owner / 责任角色
- Developer + DevOps support.
- 开发人员 + DevOps支持。

### Duration / 预计工期
- 1-2 working days.
- 1-2个工作日。

---

## 4. Data Layer and Core Domain Development
## 4. 数据层与核心领域开发

### Inputs / 输入
- Data schema v1 and module design.
- 数据结构v1与模块设计。

### Tasks / 执行任务
- [T4.1] Implement repository for license record CRUD.
- [T4.1] 实现license记录CRUD仓储层。
- [T4.2] Implement migration scripts and versioning.
- [T4.2] 实现数据库迁移脚本与版本控制。
- [T4.3] Add backup/restore and import rollback safeguards.
- [T4.3] 增加备份恢复与导入失败回滚保护。

### Outputs / 输出物
- Stable data access layer and migration scripts.
- 稳定的数据访问层与迁移脚本。
- Domain models: license, provider, server target, operation log.
- 领域模型：license、provider、server target、operation log。

### Acceptance Criteria / 验收标准
- CRUD and migration tests pass.
- CRUD与迁移测试通过。
- No data corruption in failure injection tests.
- 故障注入测试无数据损坏。

### Owner / 责任角色
- Backend developer.
- 后端开发。

### Duration / 预计工期
- 3-5 working days.
- 3-5个工作日。

---

## 5. Business Logic and Provider Adapter Development
## 5. 业务逻辑与服务商适配开发

### Inputs / 输入
- Core domain and data layer ready.
- 核心领域与数据层已就绪。

### Tasks / 执行任务
- [T5.1] Implement import pipelines:
- [T5.1] 实现导入流程：
	- Single license file + target server/path scenario
	- 单license文件+目标服务器/路径场景
	- Batch import from Excel/JSON scenario
	- Excel/JSON批量导入场景
- [T5.2] Implement parser validation, duplicate detection, and result report.
- [T5.2] 实现解析校验、重复检测、结果报告。
- [T5.3] Implement expiration calculation and reminder state generation.
- [T5.3] 实现到期计算与提醒状态生成。
- [T5.4] Implement provider adapter for start/stop with unified command interface.
- [T5.4] 通过统一命令接口实现服务商启停适配。
- [T5.5] Implement compare service across providers/servers.
- [T5.5] 实现跨服务商/服务器比对服务。

### Outputs / 输出物
- Service layer APIs and adapter implementations.
- 服务层API与适配器实现。
- Import/export and start-stop operation logs.
- 导入导出与启停操作日志。

### Acceptance Criteria / 验收标准
- Import success/failure report is generated for every run.
- 每次导入都生成成功/失败报告。
- Start/stop flow supports all target providers in baseline scope.
- 基线范围内目标服务商启停流程全部可用。
- Comparison result is deterministic for same input data.
- 相同输入下比对结果可复现。

### Owner / 责任角色
- Backend developer.
- 后端开发。

### Duration / 预计工期
- 4-7 working days.
- 4-7个工作日。

---

## 6. GUI Development and Integration
## 6. GUI开发与集成

### Inputs / 输入
- Service layer APIs and UI prototype.
- 服务层API与UI原型。

### Tasks / 执行任务
- [T6.1] Build main list view with search/filter and status highlights.
- [T6.1] 构建主列表视图，支持搜索筛选与状态高亮。
- [T6.2] Build dialogs: add/edit, import, provider start/stop, compare results.
- [T6.2] 构建弹窗：新增编辑、导入、服务商启停、比对结果。
- [T6.3] Integrate validation messages and operation feedback.
- [T6.3] 集成校验提示与操作反馈。

### Outputs / 输出物
- Complete GUI linked to business services.
- 与业务服务打通的完整GUI。

### Acceptance Criteria / 验收标准
- All P0 UI flows are operable without command line.
- 所有P0界面流程可在无命令行条件下操作。
- Invalid input has clear error prompt and recovery hint.
- 非法输入有明确报错和恢复提示。

### Owner / 责任角色
- Frontend/UI developer (Python GUI).
- 前端/UI开发（Python GUI）。

### Duration / 预计工期
- 4-6 working days.
- 4-6个工作日。

---

## 7. Testing, Hardening, and Defect Closure
## 7. 测试加固与缺陷收敛

### Inputs / 输入
- Feature complete build.
- 功能完整构建版本。

### Tasks / 执行任务
- [T7.1] Execute unit, integration, and end-to-end test plan.
- [T7.1] 执行单元、集成、端到端测试计划。
- [T7.2] Run compatibility testing on target Windows versions.
- [T7.2] 在目标Windows版本执行兼容性测试。
- [T7.3] Run stability tests for batch import and start-stop operations.
- [T7.3] 对批量导入和启停执行稳定性测试。
- [T7.4] Close defects by priority and track regression.
- [T7.4] 按优先级关闭缺陷并跟踪回归。

### Outputs / 输出物
- Test report with coverage and defect metrics.
- 含覆盖率和缺陷指标的测试报告。
- Final known issues and workaround list.
- 最终已知问题与规避方案清单。

### Acceptance Criteria / 验收标准
- Core path pass rate 100%.
- 核心路径通过率100%。
- Unit test coverage >= 70% (core modules >= 80%).
- 单元测试覆盖率>=70%（核心模块>=80%）。
- No open P0/P1 defect.
- 无未关闭P0/P1缺陷。

### Owner / 责任角色
- QA + developers.
- 测试 + 开发。

### Duration / 预计工期
- 3-5 working days.
- 3-5个工作日。

---

## 8. Packaging, Release, and Documentation
## 8. 打包发布与文档交付

### Inputs / 输入
- Release candidate build.
- 发布候选版本。

### Tasks / 执行任务
- [T8.1] Package with PyInstaller for target platform.
- [T8.1] 使用PyInstaller面向目标平台打包。
- [T8.2] Verify clean-machine installation and startup.
- [T8.2] 验证纯净机器安装与启动。
- [T8.3] Produce user guide and operation troubleshooting guide.
- [T8.3] 产出用户手册与运维排障手册。
- [T8.4] Publish release notes (features, fixes, known issues).
- [T8.4] 发布版本说明（功能、修复、已知问题）。

### Outputs / 输出物
- Installable package and checksum.
- 可安装包与校验信息。
- Release notes and operation docs.
- 版本说明与运维文档。

### Acceptance Criteria / 验收标准
- Installation success rate is 100% on target environments in validation matrix.
- 在验证矩阵中的目标环境安装成功率100%。
- User can complete core flow using documentation only.
- 用户仅依据文档可完成核心流程。

### Owner / 责任角色
- Release manager + QA.
- 发布负责人 + 测试。

### Duration / 预计工期
- 1-2 working days.
- 1-2个工作日。

---

## 9. Maintenance, Monitoring, and Iteration
## 9. 维护监控与迭代

### Inputs / 输入
- Production usage data and user feedback.
- 生产使用数据与用户反馈。

### Tasks / 执行任务
- [T9.1] Collect issue telemetry and classify enhancement requests.
- [T9.1] 收集问题日志并分类增强需求。
- [T9.2] Plan iteration backlog by value and risk.
- [T9.2] 按价值与风险规划迭代待办。
- [T9.3] Run periodic dependency and security review.
- [T9.3] 周期性进行依赖和安全审查。

### Outputs / 输出物
- Iteration roadmap and patch releases.
- 迭代路线图与补丁版本。

### Acceptance Criteria / 验收标准
- Critical bug fix SLA is met.
- 严重缺陷修复SLA达标。
- No unresolved high-risk security issue.
- 无未处理高风险安全问题。

### Owner / 责任角色
- Product owner + maintenance team.
- 产品负责人 + 维护团队。

### Duration / 预计工期
- Continuous.
- 持续进行。

---

## Milestones (Suggested)
## 里程碑（建议）
- M1: Requirements baseline signed off.
- M1：需求基线签署完成。
- M2: Architecture/data model approved, project skeleton running.
- M2：架构/数据模型通过评审，工程骨架可运行。
- M3: Core features integrated and internal test pass.
- M3：核心功能集成完成并通过内部测试。
- M4: Release candidate validated and package published.
- M4：发布候选版本验证通过并完成发布。

## Risk Register (Initial)
## 风险清单（初始）
- Provider command differences may cause start/stop incompatibility.
- 服务商命令差异导致启停不兼容。
- Remote target permission/path issues may break import/deploy.
- 远程目标权限/路径问题导致导入部署失败。
- License format diversity may reduce parser robustness.
- license格式多样导致解析鲁棒性下降。
- Mitigation: adapter contract tests, preflight checks, rollback, fallback manual mode.
- 缓解：适配器契约测试、预检查、回滚机制、手动兜底模式。

## Change Control
## 变更控制
- Any scope change must be recorded with impact on timeline, quality, and release target.
- 任何范围变更必须记录对工期、质量、发布时间的影响。
- P0 scope changes require explicit approval from product owner and tech lead.
- P0范围变更需产品负责人和技术负责人共同批准。

## Module Documents Derived from This Master Plan
## 由本总领文档派生的模块文档
- modules/README.md
- modules/M01/M01_requirements_baseline_and_design.md
- modules/M02/M02_architecture_and_technology.md
- modules/M03/M03_environment_and_ci_initialization.md
- modules/M04/M04_data_layer_and_domain.md
- modules/M05/M05_business_service_and_provider_adapter.md
- modules/M06/M06_gui_and_interaction_integration.md
- modules/M07/M07_testing_and_quality_closure.md
- modules/M08/M08_packaging_release_and_documentation.md
- modules/M09/M09_operations_monitoring_and_iteration.md

## Module Usage Rules
## 模块使用规则
- The master plan controls scope, milestones, and global quality gates.
- 总领文档负责范围、里程碑和全局质量门禁。
- Module documents are executable work packages for daily implementation and acceptance.
- 模块文档作为日常执行与验收的工作包。
- Requirement completion must be evaluated using Requirement-to-Task Alignment Matrix and module evidence.
- 需求完成判定必须结合需求-任务对齐矩阵与模块证据。
- If task or requirement IDs change, update both master and affected module docs in the same change.
- 如任务ID或需求ID变更，必须在同一次变更中同步更新总领和模块文档。

## Requirement-to-Task Alignment Matrix
## 需求到任务对齐矩阵（逐项）

| Requirement ID | Requirement Item | Aligned Tasks | Output Evidence | Acceptance Check |
| --- | --- | --- | --- | --- |
| RQ-01 | Local license CRUD (record only) / 本地license记录增删查改 | T1.1, T4.1, T6.2 | DB CRUD module, add/edit/delete UI flow | CRUD tests pass, UI flow pass |
| RQ-02 | Local extension fields (notes/tags/host id/daemon path) / 本地扩展字段 | T2.3, T4.1, T6.2 | Schema fields + edit dialog fields | Field persistence and query pass |
| RQ-03 | Import scenario A: single file + server/path / 单文件导入到目标服务器路径 | T1.1, T5.1, T5.2, T7.3 | Import pipeline log + result report | Success/failure report generated |
| RQ-04 | Import scenario B: Excel/JSON batch / Excel/JSON批量导入 | T1.1, T5.1, T5.2, T7.3 | Batch parser, dedup report, operation log | Batch import stability pass |
| RQ-05 | Export CSV/JSON/Excel / 导出CSV/JSON/Excel | T1.1, T5.2, T6.2, T7.1 | Export service + UI export action | Export file format and data integrity pass |
| RQ-06 | Expiration reminder (popup + highlight) / 到期提醒（弹窗+高亮） | T1.1, T5.3, T6.1, T6.3 | Reminder state computation + UI status display | Expiring/expired cases are correctly marked |
| RQ-07 | Search and filter / 搜索与筛选 | T1.1, T6.1, T7.1 | List filter/search implementation | Query accuracy and response pass |
| RQ-08 | Provider-aware start/stop / 多服务商启停 | T2.2, T5.4, T6.2, T7.3 | Adapter implementations + operation logs | All baseline providers pass start/stop |
| RQ-09 | Compare across providers/servers / 多服务商/服务器比对 | T1.1, T5.5, T6.2, T7.1 | Comparison service + compare result view | Same input returns deterministic result |
| RQ-10 | Non-functional quality (stability/security/maintainability) / 非功能质量 | T1.2, T2.4, T3.3, T7.4, T9.3 | Lint/test reports, log/error-code rules, security review record | No open high-risk issue, quality gates met |
| RQ-11 | User-friendly GUI / 友好GUI | T1.3, T6.1, T6.2, T6.3 | UI prototype + integrated GUI | P0 flows runnable without CLI |
| RQ-12 | Packaging and operation docs / 打包与运维文档 | T8.1, T8.2, T8.3, T8.4 | Install package, user guide, release note | Clean-machine install pass and docs usable |

## Alignment Execution Checklist
## 对齐执行检查清单
- At phase start, verify referenced requirement IDs are complete.
- 每阶段开始前，核对该阶段关联需求ID是否完整。
- At phase end, attach evidence links for each completed task ID.
- 每阶段结束后，为每个完成的任务ID附上证据链接。
- Do not mark a requirement done unless all mapped task IDs are done.
- 若映射任务ID未全部完成，不得将该需求标记为完成。
- During change request review, update both matrix row and task IDs.
- 评审需求变更时，必须同时更新矩阵行和任务ID映射。

---

This process is executable and should be used as the default delivery checklist.
本流程为可执行版本，可作为默认交付检查清单使用。
