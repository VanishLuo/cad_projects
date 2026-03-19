# M05 Business Service and Provider Adapter
# M05 业务服务与服务商适配

## Module Goal
## 模块目标
- Deliver import/export, reminder, start-stop, and compare business capabilities.
- 交付导入导出、提醒、启停、比对等业务能力

## Related Task IDs
## 关联任务ID
- T5.1, T5.2, T5.3, T5.4, T5.5

## Related Requirement IDs
## 关联需求ID
- RQ-03, RQ-04, RQ-05, RQ-06, RQ-07, RQ-08, RQ-09

## Inputs
## 输入
- M04 repository/domain
- M04仓储层与领域层。
- Provider command references and target environments
- 服务商命令参考与目标环境信息。

## Execution Tasks
## 执行任务
1. [T5.1] Implement import pipelines for single-file and batch scenarios.
1. [T5.1] 实现单文件与批量导入流程
2. [T5.2] Implement validation, deduplication, and result report generation.
2. [T5.2] 实现校验、去重与结果报告生成
3. [T5.3] Implement expiration calculation and reminder state generation.
3. [T5.3] 实现到期计算与提醒状态生成
4. [T5.4] Implement unified provider adapter interface for start/stop.
4. [T5.4] 实现统一服务商适配接口用于启停
5. [T5.5] Implement cross-provider/server comparison service.
5. [T5.5] 实现跨服务商/服务器比对服务

## T5 Working Files
## T5工作文件
- T5.1: modules/M05/M05_T5.1_import_pipeline_single_batch_v0.1.md
- T5.1：modules/M05/M05_T5.1_import_pipeline_single_batch_v0.1.md
- T5.2: modules/M05/M05_T5.2_validation_dedup_and_report_v0.1.md
- T5.2：modules/M05/M05_T5.2_validation_dedup_and_report_v0.1.md
- T5.3: modules/M05/M05_T5.3_expiration_state_engine_v0.1.md
- T5.3：modules/M05/M05_T5.3_expiration_state_engine_v0.1.md
- T5.4: modules/M05/M05_T5.4_flexnet_adapter_ssh_startstop_v0.1.md
- T5.4：modules/M05/M05_T5.4_flexnet_adapter_ssh_startstop_v0.1.md
- T5.5: modules/M05/M05_T5.5_cross_target_compare_service_v0.1.md
- T5.5：modules/M05/M05_T5.5_cross_target_compare_service_v0.1.md

## M05 Confirmation Checklist
## M05确认清单
- Import/report pipeline is complete for single and batch mode.
- 导入与报告流程在单条和批量场景中完整可用。
- FlexNet adapter via SSH account mapping is operational.
- 基于SSH账号映射的FlexNet适配器可正常运行。
- Compare results are deterministic and export-ready.
- 比对结果稳定可复现，且支持导出。
- Feature search indexes and query paths are implemented in service layer.
- 服务层已实现feature搜索索引与查询路径。
- Software design audit checklist is reviewed for this module.
- 本模块已执行软件设计规范审计清单复核。

## Outputs
## 输出物
- Service layer APIs
- 服务层API。
- Provider adapters
- 服务商适配器。
- Import/export operation reports
- 导入导出操作报告。
- Comparison result model
- 比对结果模型。

## Acceptance Criteria
## 验收标准
- Every import run generates success/failure report.
- 每次导入都输出成失败报告
- Baseline providers pass start/stop validation.
- 基线服务商启停验证通过
- Comparison output is deterministic for same inputs.
- 相同输入下比对输出可复现

## Evidence Checklist
## 证据清单
- Import report samples
- 导入报告样例。
- Adapter test logs
- 适配器测试日志。
- Comparison regression report
- 比对回归报告。

## Dependencies
## 依赖
- M04 completed
- M04已完成。

## Risks and Mitigation
## 风险与缓解
- Risk: Provider command variability.
- 风险：服务商命令差异大
- Mitigation: Add provider-specific preflight checks and fallback operations.
- 缓解：增加服务商预检查和兜底操作



