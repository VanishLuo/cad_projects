# M03 Environment and CI Initialization
# M03 环境与CI初始化

## Module Goal
## 模块目标
- Build a reproducible engineering baseline.
- 建立可复现的工程基线

## Related Task IDs
## 关联任务ID
- T3.1, T3.2, T3.3, T3.4

## Related Requirement IDs
## 关联需求ID
- RQ-10

## Inputs
## 输入
- M02 architecture and standards
- M02架构与技术标准。
- Repository access and CI platform access
- 仓库访问权限与CI平台访问权限。

## Frozen Baseline Decisions
## 冻结基线决策
- Python version: 3.11.9 at C:\tools\Python311\python.exe.
- Python版本：3.11.9，路径为C:\tools\Python311\python.exe。
- Dependency manager: uv (lock file is mandatory).
- 依赖管理：uv（必须维护锁文件）。
- CI platform: GitHub Actions.
- CI平台：GitHub Actions。
- Target OS: Windows 10/11 x64.
- 目标系统：Windows 10/11 x64。
- Quality gate: lint/format/type check must be fully green.
- 质量闸门：lint/format/type check 必须全绿。
- Coverage gate: enforce overall coverage threshold in CI.
- 覆盖率闸门：在CI中强制 overall 覆盖率阈值。

## Execution Tasks
## 执行任务
1. [T3.1] Create Python environment and dependency lock file.
1. [T3.1] 创建Python环境与依赖锁文件
2. [T3.2] Initialize project folders and base package structure.
2. [T3.2] 初始化项目目录与基础包结构
3. [T3.3] Configure lint/format/test tooling and baseline rules.
3. [T3.3] 配置lint/format/test工具与基线规则
4. [T3.4] Configure CI pipeline for static checks and unit tests.
4. [T3.4] 配置CI流水线执行静态检查与单测

## T3 Working Files
## T3工作文件
- T3.1: modules/M03/M03_T3.1_python_env_and_lock_v0.1.md
- T3.1：modules/M03/M03_T3.1_python_env_and_lock_v0.1.md
- T3.2: modules/M03/M03_T3.2_project_structure_bootstrap_v0.1.md
- T3.2：modules/M03/M03_T3.2_project_structure_bootstrap_v0.1.md
- T3.3: modules/M03/M03_T3.3_quality_tooling_baseline_v0.1.md
- T3.3：modules/M03/M03_T3.3_quality_tooling_baseline_v0.1.md
- T3.4: modules/M03/M03_T3.4_ci_pipeline_baseline_v0.1.md
- T3.4：modules/M03/M03_T3.4_ci_pipeline_baseline_v0.1.md

## Immediate Next Actions
## 立即执行项
1. Complete T3.1 and freeze dependency lock baseline.
1. 完成T3.1并冻结依赖锁定基线。
2. Complete T3.2 and verify package bootstrap run.
2. 完成T3.2并验证工程骨架可运行。
3. Complete T3.3 local quality checks.
3. 完成T3.3本地质量检查。
4. Complete T3.4 CI baseline green run.
4. 完成T3.4并达成CI基线全绿。

## M03 Confirmation Checklist
## M03确认清单
- Python runtime baseline is pinned and reproducible.
- Python运行时基线已固定且可复现。
- Layered project skeleton matches M02 architecture.
- 分层工程骨架与M02架构一致。
- Quality tooling and CI checks are aligned with M01 NFR targets.
- 质量工具与CI检查对齐M01非功能指标。
- Software design audit checklist is reviewed for this module.
- 本模块已执行软件设计规范审计清单复核。

## Outputs
## 输出物
- Environment setup guide
- 环境搭建说明。
- Project skeleton
- 工程骨架。
- CI workflow definition
- CI工作流定义。
- Quality tool configs
- 质量工具配置。

## Acceptance Criteria
## 验收标准
- New machine can run app and tests by setup guide.
- 新机器可按文档运行程序和测试
- CI baseline checks are all green.
- CI基线检查全绿

## Evidence Checklist
## 证据清单
- Setup guide verification log
- 环境搭建验证日志。
- CI run link/screenshot
- CI运行链接或截图。
- Tool configuration files snapshot
- 工具配置文件快照。

## Dependencies
## 依赖
- M02 completed
- M02已完成。

## Risks and Mitigation
## 风险与缓解
- Risk: Dependency version drift.
- 风险：依赖版本漂移
- Mitigation: Use lock file and scheduled dependency review.
- 缓解：使用锁文件并定期审查依赖



