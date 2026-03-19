# Module Document Index
# 模块文档索引

This folder decomposes the master process in development_process.md into executable module documents.
本目录将development_process.md总领流程拆解为可执行模块文档

## Mapping Rules
## 映射规则
- Task IDs are inherited from the master process: T1.1 ~ T9.3.
- 任务编号沿用总领文档：T1.1 ~ T9.3
- Requirement IDs are inherited from alignment matrix: RQ-01 ~ RQ-12.
- 需求编号沿用对齐矩阵：RQ-01 ~ RQ-12
- A requirement is completed only when all mapped task IDs are completed with evidence.
- 一个需求仅在其映射任务全部完成且有证据时才算完成
- Output format rule: every English sentence/line should be followed by one Chinese sentence/line.
- 输出格式规则：每一句英文后必须紧跟一句中文。

## Module List
## 模块清单
1. M01 Requirements Baseline and Design
1. M01 需求基线与设计
2. M02 Architecture and Technology
2. M02 架构与技术选型
3. M03 Environment and CI Initialization
3. M03 环境与CI初始化
4. M04 Data Layer and Domain
4. M04 数据层与领域模型
5. M05 Business Service and Provider Adapter
5. M05 业务服务与服务商适配
6. M06 GUI and Interaction Integration
6. M06 GUI与交互集成
7. M07 Testing and Quality Closure
7. M07 测试与质量收敛
8. M08 Packaging, Release, and Documentation
8. M08 打包发布与文档
9. M09 Operations, Monitoring, and Iteration
9. M09 运行维护与迭代

## Directory Structure
## 目录结构
- modules/M01/ contains M01 main document and T1.x working files.
- modules/M01/ 包含M01主文档与T1.x工作文件
- modules/M02/ ... modules/M09/ each contain one module main document.
- modules/M02/ ... modules/M09/ 各自包含对应模块主文档
- modules/SOFTWARE_DESIGN_AUDIT_CHECKLIST.md contains design-principle audit criteria and evidence template.
- modules/SOFTWARE_DESIGN_AUDIT_CHECKLIST.md包含设计规范审计准则与证据模板。

## Execution Order
## 执行顺序
- Default sequential order: M01 -> M09.
- 默认顺序执行：M01 -> M09
- If changed, update dependency section in each module and change log first.
- 如需调整顺序，先更新各模块依赖关系与变更记录

## Evidence Storage Suggestion
## 证据存档建议
- docs/evidence/Mxx/ should contain screenshots, reports, logs, and review records.
- docs/evidence/Mxx/ 用于存放截图、报告、日志、评审记录



