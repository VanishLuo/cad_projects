from __future__ import annotations

import os
import platform

from license_management.shared.windows_compat import collect_windows_compat_probe


def test_windows_compat_probe_has_required_runtime_fields() -> None:
    probe = collect_windows_compat_probe()

    assert probe.platform_system
    assert probe.platform_release
    assert probe.python_version
    assert probe.path_separator == os.path.sep
    assert probe.cwd
    assert probe.cwd_is_absolute is True


def test_windows_compat_probe_matches_current_platform() -> None:
    probe = collect_windows_compat_probe()

    assert probe.platform_system == platform.system()
    assert probe.python_version.startswith("3.")

    if platform.system() == "Windows":
        assert probe.supports_long_paths is True
        assert probe.path_separator == "\\"
