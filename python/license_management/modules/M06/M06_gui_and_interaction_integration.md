# M06 GUI and Interaction Integration
# M06 GUI与交互集成

## Module Goal
## 模块目标
- Deliver complete GUI workflows that call service layer without CLI dependency.
- 交付完整GUI流程，并可直接调用服务层，无需CLI依赖

## Related Task IDs
## 关联任务ID
- T6.1, T6.2, T6.3, T6.4

## Related Requirement IDs
## 关联需求ID
- RQ-01, RQ-05, RQ-06, RQ-07, RQ-08, RQ-09, RQ-11

## Inputs
## 输入
- M01 UI prototype
- M01界面原型。
- M05 service APIs
- M05服务层API。

## Execution Tasks
## 执行任务
1. [T6.1] Build list view with search/filter and expiration status highlights.
1. [T6.1] 构建列表视图，支持搜索筛选与到期状态高亮
2. [T6.2] Build dialogs for add/edit/import/start-stop/compare/export.
2. [T6.2] 构建新增编辑/导入/启停/比对/导出等弹窗
3. [T6.3] Integrate validation and operation feedback messages.
3. [T6.3] 集成输入校验与操作反馈提示
4. [T6.4] Implement feature-level search in GUI (feature name/code/keyword).
4. [T6.4] 在GUI中实现feature级搜索（feature名称/编码/关键词）。

## T6 Working Files
## T6工作文件
- T6.1: modules/M06/M06_T6.1_main_list_search_status_ui_v0.1.md
- T6.1：modules/M06/M06_T6.1_main_list_search_status_ui_v0.1.md
- T6.2: modules/M06/M06_T6.2_dialog_set_and_flow_binding_v0.1.md
- T6.2：modules/M06/M06_T6.2_dialog_set_and_flow_binding_v0.1.md
- T6.3: modules/M06/M06_T6.3_validation_and_feedback_integration_v0.1.md
- T6.3：modules/M06/M06_T6.3_validation_and_feedback_integration_v0.1.md
- T6.4: modules/M06/M06_T6.4_feature_search_ui_v0.1.md
- T6.4：modules/M06/M06_T6.4_feature_search_ui_v0.1.md

## M06 Confirmation Checklist
## M06确认清单
- GUI list/search/status interaction is complete.
- GUI列表/搜索/状态交互已完整。
- Dialog flows are fully bound to service APIs.
- 弹窗流程与服务API绑定完整。
- Validation and feedback behavior is consistent with error model.
- 校验与反馈行为与错误模型一致。
- Feature search supports feature name/code/keyword and combined filters.
- feature搜索支持名称/编码/关键词及组合筛选。
- Software design audit checklist is reviewed for this module.
- 本模块已执行软件设计规范审计清单复核。

## Outputs
## 输出物
- Integrated GUI package
- 集成后的GUI交付包。
- UI event to service API mapping list
- UI事件到服务API映射清单。
- User interaction spec update
- 用户交互规范更新。

## Acceptance Criteria
## 验收标准
- All P0 flows are operable in GUI only.
- 所有P0流程可纯GUI操作
- Invalid input has clear prompt and correction hint.
- 非法输入有明确提示与修正建议

## Evidence Checklist
## 证据清单
- UI walkthrough video/screenshots
- UI走查视频或截图。
- Interaction test checklist
- 交互测试清单。
- Error message catalog
- 错误提示目录。

## Dependencies
## 依赖
- M05 completed
- M05已完成。

## Risks and Mitigation
## 风险与缓解
- Risk: UI and service contract mismatch.
- 风险：UI与服务接口契约不一致
- Mitigation: Contract tests and typed DTO validation.
- 缓解：接口契约测试与DTO校验



