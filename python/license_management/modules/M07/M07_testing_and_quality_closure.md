# M07 Testing and Quality Closure
# M07 测试与质量收敛

## Module Goal
## 模块目标
- Verify functional and non-functional quality and close release blockers.
- 验证功能与非功能质量并清理发布阻塞项

## Related Task IDs
## 关联任务ID
- T7.1, T7.2, T7.3, T7.4

## Related Requirement IDs
## 关联需求ID
- RQ-03, RQ-04, RQ-06, RQ-08, RQ-09, RQ-10, RQ-11

## Inputs
## 输入
- Integrated build from M06
- 来自M06的集成构建版本。
- Test cases and validation matrix
- 测试用例与验证矩阵。

## Execution Tasks
## 执行任务
1. [T7.1] Execute unit/integration/E2E test plan.
1. [T7.1] 执行单元/集成/E2E测试计划
2. [T7.2] Run compatibility tests on target Windows versions.
2. [T7.2] 在目标Windows版本执行兼容性测试
3. [T7.3] Run stability tests for batch import and provider start-stop.
3. [T7.3] 对批量导入和服务商启停执行稳定性测试
4. [T7.4] Fix defects by priority and run regression tests.
4. [T7.4] 按优先级修复缺陷并执行回归

## T7 Working Files
## T7工作文件
- T7.1: modules/M07/M07_T7.1_unit_integration_e2e_plan_v0.1.md
- T7.1：modules/M07/M07_T7.1_unit_integration_e2e_plan_v0.1.md
- T7.2: modules/M07/M07_T7.2_windows_compatibility_validation_v0.1.md
- T7.2：modules/M07/M07_T7.2_windows_compatibility_validation_v0.1.md
- T7.3: modules/M07/M07_T7.3_stability_and_capacity_resilience_v0.1.md
- T7.3：modules/M07/M07_T7.3_stability_and_capacity_resilience_v0.1.md
- T7.4: modules/M07/M07_T7.4_defect_closure_and_regression_v0.1.md
- T7.4：modules/M07/M07_T7.4_defect_closure_and_regression_v0.1.md

## M07 Confirmation Checklist
## M07确认清单
- Test plan covers unit/integration/E2E layers.
- 测试计划覆盖单元/集成/E2E层级。
- Compatibility validation covers target Windows matrix.
- 兼容性验证覆盖目标Windows矩阵。
- Stability includes 20/8 baseline and upward expansion behavior.
- 稳定性测试覆盖20/8基线与向上扩展行为。
- Defect closure and regression criteria are explicit.
- 缺陷收敛与回归标准明确。
- Feature search test cases are included in functional and regression suites.
- feature搜索测试用例已纳入功能与回归套件。
- Software design audit checklist is reviewed for this module.
- 本模块已执行软件设计规范审计清单复核。

## Outputs
## 输出物
- Test report and defect trend
- 测试报告与缺陷趋势。
- Coverage report
- 覆盖率报告。
- Final known issues list
- 最终已知问题清单。

## Acceptance Criteria
## 验收标准
- Core path pass rate is 100%.
- 核心路径通过率100%。
- No open P0/P1 defects.
- 无未关闭P0/P1缺陷
- Coverage reaches baseline target.
- 覆盖率达到基线目标

## Evidence Checklist
## 证据清单
- Test execution records
- 测试执行记录。
- Defect closure report
- 缺陷关闭报告。
- Regression report
- 回归测试报告。

## Dependencies
## 依赖
- M06 completed
- M06已完成。

## Current Progress Snapshot
## 当前进度快照
- T7.1 first batch completed for integration and E2E baseline test scaffolding.
- T7.1 第一批已完成集成与E2E基线测试脚手架。
- Added integration coverage for GUI-service binding across import, search, and operation feedback.
- 新增 GUI-服务绑定的集成覆盖，包含导入、搜索与操作反馈。
- Added E2E user-journey tests for core flow and invalid-input recovery path.
- 新增核心流程与非法输入恢复路径的 E2E 用户旅程测试。
- T7.1 second batch completed with E2E search/filter matrix and Windows compatibility probes.
- T7.1 第二批已完成，补充 E2E 搜索/筛选矩阵与 Windows 兼容性探针。

## Next Action
## 下一步
- Start T7.2 execution: expand Windows version/deployment matrix and capture compatibility evidence reports.
- 开始执行 T7.2：扩展 Windows 版本/部署矩阵，并沉淀兼容性证据报告。

## Risks and Mitigation
## 风险与缓解
- Risk: Late defects delay release.
- 风险：后期缺陷导致发布延期
- Mitigation: Daily defect triage and strict entry/exit criteria.
- 缓解：每日缺陷分级与严格出入口标准





