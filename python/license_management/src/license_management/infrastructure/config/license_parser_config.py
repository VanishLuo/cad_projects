from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import cast


@dataclass(slots=True, frozen=True)
class ParserProfileConfig:
    feature_keyword: str
    feature_name_token_index: int
    quantity_regexes: tuple[str, ...]
    expiry_regexes: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class ParserRouteConfig:
    provider_pattern: str
    vendor_pattern: str
    profile: str


@dataclass(slots=True, frozen=True)
class LicenseParserConfig:
    default_profile: str
    profiles: dict[str, ParserProfileConfig]
    routes: tuple[ParserRouteConfig, ...]


@lru_cache(maxsize=1)
def load_license_parser_config() -> LicenseParserConfig:
    config_path = Path(__file__).resolve().parents[2] / "config" / "license_parser_profiles.json"
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    data = _to_str_object_dict(raw)

    profiles_raw = _to_str_object_dict(data.get("profiles"))
    profiles: dict[str, ParserProfileConfig] = {}
    for profile_name, profile_value in profiles_raw.items():
        profile_dict = _to_str_object_dict(profile_value)
        profiles[profile_name] = ParserProfileConfig(
            feature_keyword=str(profile_dict.get("feature_keyword", "FEATURE")).strip()
            or "FEATURE",
            feature_name_token_index=_to_non_negative_int(
                profile_dict.get("feature_name_token_index"),
                default=1,
            ),
            quantity_regexes=_to_str_tuple(profile_dict.get("quantity_regexes")),
            expiry_regexes=_to_str_tuple(profile_dict.get("expiry_regexes")),
        )

    if not profiles:
        profiles["default"] = ParserProfileConfig(
            feature_keyword="FEATURE",
            feature_name_token_index=1,
            quantity_regexes=(r"\\b(?:COUNT|QTY|QUANTITY)\\s*=\\s*(\\d+)\\b",),
            expiry_regexes=(r"\\b(\\d{4}-\\d{2}-\\d{2})\\b", r"\\b(\\d{4}/\\d{2}/\\d{2})\\b"),
        )

    default_profile = str(data.get("default_profile", "default")).strip() or "default"
    if default_profile not in profiles:
        default_profile = next(iter(profiles.keys()))

    routes_raw = data.get("routes")
    routes: list[ParserRouteConfig] = []
    if isinstance(routes_raw, list):
        typed_routes = cast(list[object], routes_raw)
        for item in typed_routes:
            item_dict = _to_str_object_dict(item)
            profile = str(item_dict.get("profile", "")).strip()
            if profile == "" or profile not in profiles:
                continue
            routes.append(
                ParserRouteConfig(
                    provider_pattern=str(item_dict.get("provider", "*")).strip() or "*",
                    vendor_pattern=str(item_dict.get("vendor", "*")).strip() or "*",
                    profile=profile,
                )
            )

    if not routes:
        routes.append(
            ParserRouteConfig(provider_pattern="*", vendor_pattern="*", profile=default_profile)
        )

    return LicenseParserConfig(
        default_profile=default_profile,
        profiles=profiles,
        routes=tuple(routes),
    )


def _to_non_negative_int(value: object, *, default: int) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _to_str_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    typed = cast(list[object], value)
    normalized: list[str] = []
    for item in typed:
        text = str(item).strip()
        if text:
            normalized.append(text)
    return tuple(normalized)


def _to_str_object_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    typed = cast(dict[object, object], value)
    result: dict[str, object] = {}
    for key, item in typed.items():
        if isinstance(key, str):
            result[key] = item
    return result
