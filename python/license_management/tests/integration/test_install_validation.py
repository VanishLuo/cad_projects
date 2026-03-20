from __future__ import annotations

from pathlib import Path

from license_management.shared.install_validation import validate_clean_machine_install


def test_clean_machine_install_validation_passes_when_files_exist(tmp_path: Path) -> None:
    install_dir = tmp_path / "install"
    install_dir.mkdir()
    (install_dir / "license-management.exe").write_text("bin", encoding="utf-8")
    (install_dir / "uninstall.bat").write_text("echo uninstall", encoding="utf-8")

    report = validate_clean_machine_install(
        environment="windows-11-clean",
        install_dir=install_dir,
        executable_name="license-management.exe",
    )

    assert report.environment == "windows-11-clean"
    assert report.pass_rate == 1.0


def test_clean_machine_install_validation_fails_when_missing_files(tmp_path: Path) -> None:
    install_dir = tmp_path / "empty"
    install_dir.mkdir()

    report = validate_clean_machine_install(
        environment="windows-10-clean",
        install_dir=install_dir,
        executable_name="license-management.exe",
    )

    assert report.pass_rate < 1.0
    assert any(not item.passed for item in report.checks)
