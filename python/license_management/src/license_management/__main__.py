"""Application launcher entrypoint.

This module centralizes startup behavior for CLI and GUI mode.
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _ensure_src_on_sys_path() -> None:
    """Support direct file execution in IDEs."""
    current_file = Path(__file__).resolve()
    # Resolve source root from this file location.
    # 从当前文件位置解析出 src 根目录。
    src_dir = current_file.parent.parent
    # Only update sys.path when src path is missing to avoid redundant path changes.
    # 仅在 src 路径缺失时才更新 sys.path，避免重复修改路径。
    src_str = str(src_dir)
    if src_str not in sys.path:
        # Prepend src so package imports work when this file is run directly.
        # 将 src 插入最前面，确保直接运行当前文件时包导入可用。
        sys.path.insert(0, src_str)


def _resolve_version() -> str:
    """Resolve package version and fallback to dev."""
    try:
        return version("license-management")
    except PackageNotFoundError:
        return "dev"


def main(argv: list[str] | None = None) -> int:
    """Program entry function."""
    _ensure_src_on_sys_path()

    # Define entry-level CLI flags shared by all startup paths.
    # 定义入口级命令行参数，供所有启动路径共用。
    parser = argparse.ArgumentParser(description="license-management launcher")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print application version and exit.",
    )

    # Use provided argv for tests/callers; otherwise parse real command-line args.
    # 测试或调用方可传入 argv；否则解析真实命令行参数。
    args = parser.parse_args(argv)

    # Version output is handled before GUI import/startup.
    # 版本输出在 GUI 导入/启动前处理。
    app_version = _resolve_version()
    if args.version:
        print(f"license-management {app_version}")
        return 0

    try:
        from license_management.gui.bootstrap import run_gui
    except ImportError as exc:
        print("Failed to start GUI mode.")
        print(f"Import error: {exc}")
        print("Ensure project venv is active and PyQt5 is installed.")
        return 1

    return run_gui()


if __name__ == "__main__":
    # Use SystemExit to return exit code from main() when run as a script.
    # 作为脚本运行时，使用 SystemExit 返回 main() 的退出码。
    raise SystemExit(main())
