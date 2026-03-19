# Software Design Compliance Audit Checklist
# 软件设计规范审计清单

## Audit Scope
## 审计范围
- Architecture quality, module boundaries, extensibility, reliability, and security.
- 架构质量、模块边界、可扩展性、可靠性与安全性。
- Requirement-to-implementation traceability and testability.
- 需求到实现的可追溯性与可测试性。

## Audit Principles
## 审计原则
- Principle 1: Modularity.
- 原则1：模块化。
- Principle 2: Separation of concerns.
- 原则2：关注点分离。
- Principle 3: Extensibility.
- 原则3：可扩展性。
- Principle 4: Testability.
- 原则4：可测试性。
- Principle 5: Observability.
- 原则5：可观测性。
- Principle 6: Security.
- 原则6：安全性。
- Principle 7: Robust error handling.
- 原则7：健壮错误处理。
- Principle 8: Maintainability and readability.
- 原则8：可维护性与可读性。

## Checklist
## 检查清单
- Layer boundaries are explicit and enforced.
- 分层边界明确且有强制约束。
- GUI does not bypass service/domain policies.
- GUI不会绕过服务层/领域层策略。
- Provider adapter is isolated and pluggable.
- 服务商适配器隔离且可插拔。
- SSH account mapping and audit trail are complete.
- SSH账号映射与审计轨迹完整。
- Search includes feature-level retrieval and combined filters.
- 搜索能力包含feature级检索与组合筛选。
- Capacity policy supports stable baseline and upward redundancy mode.
- 容量策略支持稳定基线与向上冗余模式。
- Critical flows have unit/integration/E2E test coverage mapping.
- 关键流程具备单元/集成/E2E测试覆盖映射。
- Logs and error codes are standardized and actionable.
- 日志与错误码标准化且可定位问题。

## Audit Evidence Template
## 审计证据模板
- Item:
- 条目：
- Severity: High/Medium/Low
- 严重级别：高/中/低
- Finding:
- 发现：
- Action owner:
- 责任人：
- Closure evidence link:
- 闭环证据链接：
- Status: Open/Closed
- 状态：未关闭/已关闭
