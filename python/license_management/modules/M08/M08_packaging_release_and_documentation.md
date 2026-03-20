# M08 Packaging, Release, and Documentation
# M08 打包发布与文档

## Module Goal
## 模块目标
- Produce releasable package and complete operation documents.
- 产出可发布安装包与完整操作文档

## Related Task IDs
## 关联任务ID
- T8.1, T8.2, T8.3, T8.4

## Related Requirement IDs
## 关联需求ID
- RQ-12

## Inputs
## 输入
- Release candidate from M07
- 来自M07的发布候选版本。
- Target environment matrix
- 目标环境验证矩阵。

## Execution Tasks
## 执行任务
1. [T8.1] Package application using PyInstaller.
1. [T8.1] 使用PyInstaller打包应用
2. [T8.2] Verify clean-machine install/start and uninstall behavior.
2. [T8.2] 验证纯净机器安装/启动与卸载行为
3. [T8.3] Deliver user guide and operation troubleshooting guide.
3. [T8.3] 交付用户手册与运维排障手册
4. [T8.4] Publish release notes with features/fixes/known issues.
4. [T8.4] 发布包含功能/修复/已知问题的版本说明

## T8 Working Files
## T8工作文件
- T8.1: modules/M08/M08_T8.1_packaging_pipeline_v0.1.md
- T8.1：modules/M08/M08_T8.1_packaging_pipeline_v0.1.md
- T8.2: modules/M08/M08_T8.2_clean_machine_install_validation_v0.1.md
- T8.2：modules/M08/M08_T8.2_clean_machine_install_validation_v0.1.md
- T8.3: modules/M08/M08_T8.3_user_and_ops_docs_delivery_v0.1.md
- T8.3：modules/M08/M08_T8.3_user_and_ops_docs_delivery_v0.1.md
- T8.4: modules/M08/M08_T8.4_release_notes_and_publish_v0.1.md
- T8.4：modules/M08/M08_T8.4_release_notes_and_publish_v0.1.md

## M08 Confirmation Checklist
## M08确认清单
- Packaging output is reproducible and verifiable.
- 打包产物可复现且可验证。
- Clean-machine install/uninstall is validated.
- 纯净机安装与卸载已验证。
- User and ops docs are complete for P0 paths.
- 用户与运维文档覆盖P0路径。
- Release notes are traceable to delivered artifacts.
- 版本说明可追溯到交付产物。
- Software design audit checklist is reviewed for this module.
- 本模块已执行软件设计规范审计清单复核。

## Outputs
## 输出物
- Install package and checksum
- 安装包与校验信息。
- Release notes
- 版本说明。
- User and operation guides
- 用户手册与运维手册。

## Acceptance Criteria
## 验收标准
- Install success rate is 100% in validation matrix.
- 验证矩阵中安装成功率100%
- Documentation is sufficient for independent operation.
- 文档足以支持独立操作

## Evidence Checklist
## 证据清单
- Installation verification records
- 安装验证记录。
- Package checksum record
- 包校验记录。
- Documentation review sign-off
- 文档评审签署记录。

## Dependencies
## 依赖
- M07 completed
- M07已完成。

## Current Progress Snapshot
## 当前进度快照
- T8.1 first batch completed with packaging manifest/checksum utility and integration tests.
- T8.1 第一批已完成，交付打包清单/校验工具与集成测试。
- Added manifest generation and checksum write path for release artifact verification.
- 已新增发布制品清单生成与校验写出路径，用于产物校验。
- T8.2 completed with clean-machine installation validation utility and tests.
- T8.2 已完成，交付净机安装验证工具与测试。
- T8.3 completed with user guide and operations runbook delivery.
- T8.3 已完成，已交付用户手册与运维手册。
- T8.4 completed with release note/publish record utility and release note sample.
- T8.4 已完成，交付发布说明/发布记录工具与发布说明样例。

## Next Action
## 下一步
- M08 module closure completed; hand over to M09 operations cadence execution.
- M08 模块已完成收敛，进入 M09 运维节奏执行。

## Risks and Mitigation
## 风险与缓解
- Risk: Packaging misses runtime dependencies.
- 风险：打包遗漏运行时依赖
- Mitigation: Clean-machine validation and dependency manifest check.
- 缓解：纯净机验证和依赖清单核对



