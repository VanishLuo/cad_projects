from __future__ import annotations

from pathlib import Path

import pytest

from license_management.shared.windows_compat import validate_deployment_profile


@pytest.mark.parametrize(
    ("profile_name", "is_supported"),
    [
        ("desktop-installer", True),
        ("portable-zip", True),
        ("enterprise-rollout", True),
        ("custom-unknown", False),
    ],
)
def test_windows_deployment_profile_matrix(profile_name: str, is_supported: bool) -> None:
    result = validate_deployment_profile(profile_name, str(Path.cwd()))

    assert result.profile_name == profile_name
    assert result.install_dir_is_absolute is True
    assert result.install_dir_exists is True
    assert result.is_supported is is_supported
