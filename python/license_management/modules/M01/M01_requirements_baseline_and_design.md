# M01 Requirements Baseline and Design
# M01 需求基线与设计

## Module Goal
## 模块目标
- Freeze product scope and produce signed baseline.
- 冻结产品范围并产出签字基线

## Role Alignment
## 角色对齐
- Owner + Executor: CAD engineer (you)
- 负责人 + 执行人：CAD工程师（你）
- Copilot role: planning assistant, document drafter, checklist reviewer, risk reminder
- Copilot角色：计划助手、文档起草、检查清单复核、风险提醒。

## Collaboration Mode
## 协作方式
- You make final decisions and approvals.
- 你负责最终决策与审批
- I prepare drafts/templates, provide gap analysis, and maintain traceability links.
- 我负责准备草案模板、差距分析、维护可追踪映射。
- For each task ID, you can ask me for: input checklist, output template, acceptance review.
- 对每个任务ID，你都可以让我提供：输入清单、输出模板、验收复核

## Related Task IDs
## 关联任务ID
- T1.1, T1.2, T1.3, T1.4

## Related Requirement IDs
## 关联需求ID
- RQ-01, RQ-03, RQ-04, RQ-05, RQ-06, RQ-07, RQ-09, RQ-10, RQ-11

## Inputs
## 输入
- requirements_and_design.md
- Stakeholder interview notes
- Existing license operation constraints

## Execution Tasks
## 执行任务
1. [T1.1] Freeze functional scope and identify out-of-scope items.
1. [T1.1] 冻结功能范围并明确范围外事项
2. [T1.2] Define non-functional targets and measurable thresholds.
2. [T1.2] 定义非功能目标及可量化阈值
3. [T1.3] Produce UI interaction draft for core flows.
3. [T1.3] 产出核心流程UI交互草图
4. [T1.4] Run review meeting and baseline sign-off.
4. [T1.4] 组织评审并完成基线签署

## Single-Owner Execution Notes
## 单负责人执行说明
- T1.1: Build one-page scope boundary list first, then freeze P0/P1/P2.
- T1.1：先产出一页范围边界清单，再冻结P0/P1/P2
- T1.2: Define measurable thresholds only (e.g., response time, defect closure SLA).
- T1.2：仅定义可量化阈值（如响应时间、缺陷关闭SLA）
- T1.3: Keep prototype lightweight, focus on core paths (list/import/start-stop/compare).
- T1.3：原型保持轻量，聚焦核心路径（列表/导入/启停/比对）。
- T1.4: Replace multi-party sign-off with owner sign-off + review record.
- T1.4：将多人签署改为负责人签署 + 评审记录留痕。

## T1.1 Working Files
## T1.1工作文件
- Template: modules/M01/M01_T1.1_scope_boundary_template.md
- 模板：modules/M01/M01_T1.1_scope_boundary_template.md
- Draft baseline: modules/M01/M01_T1.1_scope_boundary_baseline_v0.1.md
- 草案：modules/M01/M01_T1.1_scope_boundary_baseline_v0.1.md

## T1.2 Working Files
## T1.2工作文件
- Measurable targets sheet: modules/M01/M01_T1.2_measurable_targets_v0.1.md
- 可量化指标表：modules/M01/M01_T1.2_measurable_targets_v0.1.md

## T1.3 Working Files
## T1.3工作文件
- UI interaction draft: modules/M01/M01_T1.3_ui_interaction_draft_v0.2.md
- UI交互草图：modules/M01/M01_T1.3_ui_interaction_draft_v0.2.md

## T1.4 Working Files
## T1.4工作文件
- Baseline review and sign-off package: modules/M01/M01_T1.4_baseline_review_signoff_package_v0.1.md
- 基线评审与签署包：modules/M01/M01_T1.4_baseline_review_signoff_package_v0.1.md

## Immediate Next Actions
## 立即执行项
1. Complete owner sign-off in T1.2 measurable targets sheet.
1. 完成T1.2可量化指标表的负责人签署
2. Execute T1.4 review gate checklist and fill sign-off statement.
2. 执行T1.4评审闸门清单并填写签署声明
3. After T1.4 sign-off, hand off approved baseline package to M02.
3. T1.4签署后，将已批准基线包移交M02

## Outputs
## 输出物
- Requirement baseline v1.0
- Feature priority list (P0/P1/P2)
- UI prototype (main list/import/start-stop/compare)
- Requirement change log initialized

## Acceptance Criteria
## 验收标准
- Scope has no unresolved conflict.
- 所有范围冲突均已闭环
- Every P0 feature has clear success criteria.
- 每个P0功能有清晰成功判定
- Baseline is signed by owner (CAD engineer) and reviewed with recorded comments.
- 基线由负责人（CAD工程师）签署，并保留评审意见记录
- Feature search requirement is explicitly defined in requirements baseline.
- 需求基线中已明确feature搜索要求。

## Evidence Checklist
## 证据清单
- Signed meeting minutes
- Baseline document hash/version
- Prototype screenshots

## Dependencies
## 依赖
- None

## Risks and Mitigation
## 风险与缓解
- Risk: Ambiguous provider capabilities.
- 风险：服务商能力边界不清
- Mitigation: Add provider capability matrix in review.
- 缓解：评审时补充服务商能力矩阵

## Design Audit Reference
## 设计审计引用
- Apply modules/SOFTWARE_DESIGN_AUDIT_CHECKLIST.md for M01 compliance review.
- 使用modules/SOFTWARE_DESIGN_AUDIT_CHECKLIST.md执行M01规范审计。



