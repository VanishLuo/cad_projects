from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(slots=True, frozen=True)
class DependencyFinding:
    package: str
    version: str
    risk: str
    recommendation: str


@dataclass(slots=True, frozen=True)
class SecurityReviewReport:
    review_date: str
    findings: tuple[DependencyFinding, ...]

    @property
    def high_risk_count(self) -> int:
        return sum(1 for item in self.findings if item.risk == "high")


def build_security_review_report(findings: list[DependencyFinding]) -> SecurityReviewReport:
    return SecurityReviewReport(
        review_date=date.today().isoformat(),
        findings=tuple(findings),
    )


def write_security_review_report(report: SecurityReviewReport, output_path: Path) -> None:
    payload = {
        "review_date": report.review_date,
        "high_risk_count": report.high_risk_count,
        "findings": [
            {
                "package": item.package,
                "version": item.version,
                "risk": item.risk,
                "recommendation": item.recommendation,
            }
            for item in report.findings
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
