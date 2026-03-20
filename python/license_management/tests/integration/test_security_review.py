from __future__ import annotations

import json
from pathlib import Path

from license_management.shared.security_review import (
    DependencyFinding,
    build_security_review_report,
    write_security_review_report,
)


def test_security_review_report_counts_high_risk(tmp_path: Path) -> None:
    report = build_security_review_report(
        [
            DependencyFinding("pyinstaller", "6.6.0", "medium", "Review changelog"),
            DependencyFinding("legacy-lib", "1.2.0", "high", "Upgrade to >=1.3.5"),
        ]
    )

    assert report.high_risk_count == 1

    output = tmp_path / "security_review.json"
    write_security_review_report(report, output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["high_risk_count"] == 1
    assert len(payload["findings"]) == 2
