from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class InstallCheck:
    name: str
    passed: bool
    detail: str


@dataclass(slots=True, frozen=True)
class CleanMachineValidationReport:
    environment: str
    checks: tuple[InstallCheck, ...]

    @property
    def pass_rate(self) -> float:
        if not self.checks:
            return 0.0
        passed = sum(1 for item in self.checks if item.passed)
        return passed / len(self.checks)


def validate_clean_machine_install(
    *,
    environment: str,
    install_dir: Path,
    executable_name: str,
) -> CleanMachineValidationReport:
    executable = install_dir / executable_name
    uninstall_script = install_dir / "uninstall.bat"

    checks = (
        InstallCheck(
            name="install_dir_exists",
            passed=install_dir.exists(),
            detail=f"install_dir={install_dir}",
        ),
        InstallCheck(
            name="executable_present",
            passed=executable.exists(),
            detail=f"executable={executable}",
        ),
        InstallCheck(
            name="uninstall_entry_present",
            passed=uninstall_script.exists(),
            detail=f"uninstall={uninstall_script}",
        ),
    )

    return CleanMachineValidationReport(environment=environment, checks=checks)
