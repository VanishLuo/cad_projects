# M04 Data Layer and Domain
# M04 数据层与领域模型

## Module Goal
## 模块目标
- Deliver stable data access and domain model foundation.
- 交付稳定的数据访问层与领域模型基础

## Related Task IDs
## 关联任务ID
- T4.1, T4.2, T4.3

## Related Requirement IDs
## 关联需求ID
- RQ-01, RQ-02

## Inputs
## 输入
- M02 schema and migration strategy
- M02数据结构与迁移策略。
- M03 project skeleton
- M03工程骨架。

## Execution Tasks
## 执行任务
1. [T4.1] Implement repository for local license CRUD and query filters.
1. [T4.1] 实现本地license记录CRUD与查询筛选仓储
2. [T4.2] Implement migration scripts and schema version tracking.
2. [T4.2] 实现迁移脚本与结构版本跟踪
3. [T4.3] Implement backup/restore and rollback on import failure.
3. [T4.3] 实现备份恢复及导入失败回滚机制

## T4 Working Files
## T4工作文件
- T4.1: modules/M04/M04_T4.1_repository_crud_and_query_v0.1.md
- T4.1：modules/M04/M04_T4.1_repository_crud_and_query_v0.1.md
- T4.2: modules/M04/M04_T4.2_migration_and_versioning_v0.1.md
- T4.2：modules/M04/M04_T4.2_migration_and_versioning_v0.1.md
- T4.3: modules/M04/M04_T4.3_backup_restore_and_rollback_v0.1.md
- T4.3：modules/M04/M04_T4.3_backup_restore_and_rollback_v0.1.md

## M04 Confirmation Checklist
## M04确认清单
- CRUD and filter query contracts are stable.
- CRUD与筛选查询契约稳定。
- Migration strategy is reproducible and versioned.
- 迁移策略可复现且具备版本控制。
- Backup/rollback path satisfies controlled edit safety.
- 备份与回滚路径满足受控修改安全要求。
- Software design audit checklist is reviewed for this module.
- 本模块已执行软件设计规范审计清单复核。

## Outputs
## 输出物
- Repository interfaces and implementations
- 仓储接口与实现。
- Migration package
- 迁移脚本包。
- Backup and rollback utility
- 备份与回滚工具。

## Acceptance Criteria
## 验收标准
- CRUD and migration tests pass.
- CRUD与迁移测试通过
- Failure injection tests show no data corruption.
- 故障注入测试无数据损坏

## Evidence Checklist
## 证据清单
- Unit test report
- 单元测试报告。
- Migration test report
- 迁移测试报告。
- Rollback test logs
- 回滚测试日志。

## Dependencies
## 依赖
- M03 completed
- M03已完成。

## Risks and Mitigation
## 风险与缓解
- Risk: Schema changes break compatibility.
- 风险：数据结构变更破坏兼容
- Mitigation: Use explicit migration IDs and backward-compatible scripts.
- 缓解：使用明确迁移ID与向后兼容脚本



