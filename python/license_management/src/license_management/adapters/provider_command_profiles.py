"""Provider start-option profile loader and resolver.

This module centralizes provider-specific command option rules used to compose
startup commands and reads them from an external JSON file so option changes
do not require source-code edits.

Config source:
        src/license_management/config/provider_start_options.json

Supported keys:
        - start_file_option: primary option before license file path
        - log_option: optional log option token
        - log_file_template: optional log file template
            placeholders:
                - {date}: current date in YYYY-MM-DD
                - {license_dir}: directory of license_file_path

Design notes:
        - Provider matching is case-insensitive
        - Missing provider falls back to default profile
        - Config is cached by lru_cache(maxsize=1)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from functools import lru_cache
import ntpath
from pathlib import Path
from typing import cast


@dataclass(slots=True, frozen=True)
class ProviderCommandProfile:
    """Resolved option profile for one provider."""

    start_file_option: str
    log_option: str = ""
    log_file_template: str = ""


@dataclass(slots=True, frozen=True)
class ProviderCommandProfileConfig:
    """In-memory profile map."""

    default: ProviderCommandProfile
    providers: dict[str, ProviderCommandProfile]


@lru_cache(maxsize=1)
def _load_profiles() -> ProviderCommandProfileConfig:
    """Load and normalize profiles from JSON.

    Returns a usable config object even when raw JSON is partially malformed.
    """

    config_path = Path(__file__).resolve().parents[1] / "config" / "provider_start_options.json"
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        # Safe fallback if config file contains a non-object payload.
        return ProviderCommandProfileConfig(
            default=ProviderCommandProfile(start_file_option="-c"),
            providers={},
        )
    data = cast(dict[object, object], raw)

    default_obj_raw = data.get("default", {})
    default_obj = _to_str_object_dict(default_obj_raw)
    default_option = str(default_obj.get("start_file_option", "-c")).strip() or "-c"
    default_log_option = str(default_obj.get("log_option", "")).strip()
    default_log_template = str(default_obj.get("log_file_template", "")).strip()
    default_profile = ProviderCommandProfile(
        start_file_option=default_option,
        log_option=default_log_option,
        log_file_template=default_log_template,
    )

    raw_providers_obj = data.get("providers", {})
    raw_providers_untyped = _to_str_object_dict(raw_providers_obj)
    providers: dict[str, ProviderCommandProfile] = {}
    for name, profile_obj_raw in raw_providers_untyped.items():
        profile_obj = _to_str_object_dict(profile_obj_raw)
        if not profile_obj:
            continue
        option = str(profile_obj.get("start_file_option", default_option)).strip() or default_option
        log_option = str(profile_obj.get("log_option", default_log_option)).strip()
        log_template = str(profile_obj.get("log_file_template", default_log_template)).strip()
        providers[name.strip().lower()] = ProviderCommandProfile(
            start_file_option=option,
            log_option=log_option,
            log_file_template=log_template,
        )

    return ProviderCommandProfileConfig(default=default_profile, providers=providers)


def resolve_start_option_tokens(
    provider: str,
    *,
    today: date | None = None,
    license_file_path: str = "",
) -> tuple[str, ...]:
    """Resolve full option token tuple.

    Output format:
        (start_file_option,) or
        (start_file_option, log_option, resolved_log_file)

    Placeholder expansion:
        {date} -> YYYY-MM-DD
        {license_dir} -> directory of license_file_path
    """

    config = _load_profiles()
    profile = config.providers.get(provider.strip().lower(), config.default)
    tokens: list[str] = [profile.start_file_option]
    if profile.log_option and profile.log_file_template:
        now = today or date.today()
        license_dir = ntpath.dirname(license_file_path)
        log_file = (
            profile.log_file_template.replace("{date}", now.isoformat())
            .replace("{license_dir}", license_dir)
            .replace("//", "/")
        )
        tokens.extend([profile.log_option, log_file])
    return tuple(tokens)


def _to_str_object_dict(value: object) -> dict[str, object]:
    """Normalize unknown object to dict[str, object]."""

    if not isinstance(value, dict):
        return {}

    typed = cast(dict[object, object], value)
    normalized: dict[str, object] = {}
    for key, item in typed.items():
        if isinstance(key, str):
            normalized[key] = item
    return normalized
