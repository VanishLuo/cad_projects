# M02 Architecture and Technology
# M02 架构与技术选型

## Module Goal
## 模块目标
- Produce implementable architecture and technical standards.
- 产出可落地架构与技术标准

## Role Alignment
## 角色对齐
- Owner + Executor: CAD engineer (you)
- 负责人 + 执行人：CAD工程师（你）
- Copilot role: architecture drafting assistant, checklist reviewer, consistency guard
- Copilot角色：架构草案助手、检查清单复核、口径一致性守护。

## Collaboration Mode
## 协作方式
- You finalize decisions and sign-off.
- 你负责最终决策与签署
- I draft artifacts, track links, and run consistency checks.
- 我负责起草文档、维护关联链接、执行一致性检查

## Related Task IDs
## 关联任务ID
- T2.1, T2.2, T2.3, T2.4

## Related Requirement IDs
## 关联需求ID
- RQ-02, RQ-08, RQ-10

## Inputs
## 输入
- M01 baseline package
- Initial performance and security targets

## Execution Tasks
## 执行任务
1. [T2.1] Confirm runtime stack and compatibility matrix.
1. [T2.1] 确认运行栈与兼容矩阵
2. [T2.2] Define layered architecture and module ownership.
2. [T2.2] 定义分层架构与模块职责
3. [T2.3] Define schema, index, constraints, and migration strategy.
3. [T2.3] 定义数据结构、索引、约束与迁移策略
4. [T2.4] Define log format, error code, and exception taxonomy.
4. [T2.4] 定义日志格式、错误码与异常分层

## Single-Owner Execution Notes
## 单负责人执行说明
- T2.1: Freeze runtime stack first, avoid mid-stage framework swaps.
- T2.1：先冻结运行栈，避免中途切换框架
- T2.2: Keep provider adapter isolated; FlexNet baseline implementation must not leak into GUI/business core.
- T2.2：保持服务商适配隔离；FlexNet基线实现不得渗透GUI/业务核心
- T2.3: Keep schema extensible with migration discipline.
- T2.3：在迁移纪律下保持数据结构可扩展
- T2.4: Make logs and error codes directly usable for ops troubleshooting.
- T2.4：日志与错误码要可直接支撑运维排障

## T2.1 Working Files
## T2.1工作文件
- Runtime stack and compatibility matrix: modules/M02/M02_T2.1_runtime_stack_and_compatibility_v0.1.md
- 运行栈与兼容矩阵：modules/M02/M02_T2.1_runtime_stack_and_compatibility_v0.1.md

## T2.2 Working Files
## T2.2工作文件
- Layered architecture and module ownership: modules/M02/M02_T2.2_layered_architecture_and_ownership_v0.1.md
- 分层架构与模块职责：modules/M02/M02_T2.2_layered_architecture_and_ownership_v0.1.md

## T2.3 Working Files
## T2.3工作文件
- Schema, constraints, and migration strategy: modules/M02/M02_T2.3_schema_constraints_and_migration_v0.1.md
- 数据结构、约束与迁移策略：modules/M02/M02_T2.3_schema_constraints_and_migration_v0.1.md

## T2.4 Working Files
## T2.4工作文件
- Logging, error code, and exception taxonomy: modules/M02/M02_T2.4_logging_errorcode_and_exception_taxonomy_v0.1.md
- 日志、错误码与异常分层：modules/M02/M02_T2.4_logging_errorcode_and_exception_taxonomy_v0.1.md

## Immediate Next Actions
## 立即执行项
1. Confirm T2.1 stack freeze and compatibility baseline.
1. 确认T2.1运行栈冻结与兼容基线
2. Confirm T2.2 layered boundaries and adapter contracts.
2. 确认T2.2分层边界与适配器契约
3. Confirm T2.3 schema and migration baseline.
3. 确认T2.3数据结构与迁移基线
4. Confirm T2.4 observability standards (log/error/exception).
4. 确认T2.4可观测性标准（日志/错误/异常）
5. After T2.1-T2.4 sign-off, hand off to M03.
5. T2.1-T2.4签署后移交M03

## M02 Confirmation Checklist
## M02确认清单
- FlexNet baseline + future provider extension interface are both preserved.
- FlexNet基线与后续服务商扩展接口均已保留
- SSH account-based operations are reflected in architecture and error model.
- 基于SSH账号的操作已映射到架构与错误模型
- Capacity policy is consistent: stable 20/8 + upward expansion mode.
- 容量策略口径一致：稳定20/8 + 向上扩展模式

## Outputs
## 输出物
- Architecture diagram
- 架构图。
- Data schema v1
- 数据结构v1。
- Provider adapter interface contract
- 服务商适配器接口契约。
- Logging and error code specification
- 日志与错误码规范。

## Acceptance Criteria
## 验收标准
- Core scenarios are fully mapped to modules.
- 核心场景已完整映射到模块
- New provider integration requires no core flow change.
- 新服务商接入不改核心流程
- Schema supports required extension fields.
- 数据结构支持扩展字段需求

## Evidence Checklist
## 证据清单
- Architecture review record
- 架构评审记录。
- DB schema review record
- 数据库结构评审记录。
- API/interface contract document
- API/接口契约文档。

## Dependencies
## 依赖
- M01 completed
- M01已完成。

## Risks and Mitigation
## 风险与缓解
- Risk: Over-coupled provider implementation.
- 风险：服务商实现耦合过高
- Mitigation: Enforce adapter contract tests before merge.
- 缓解：合并前强制适配器契约测试

## Design Audit Reference
## 设计审计引用
- Apply modules/SOFTWARE_DESIGN_AUDIT_CHECKLIST.md for architecture compliance review.
- 使用modules/SOFTWARE_DESIGN_AUDIT_CHECKLIST.md执行架构规范审计。





