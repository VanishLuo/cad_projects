from __future__ import annotations

from datetime import date
from pathlib import Path
from pytest import MonkeyPatch

from license_management.application.license_file_parser import (
    LicenseParserResolver,
    LicenseFeatureParser,
)
from license_management.infrastructure.config.license_parser_config import (
    LicenseParserConfig,
    ParserProfileConfig,
    ParserRouteConfig,
)


def test_license_feature_parser_extracts_feature_name_quantity_and_expiry(tmp_path: Path) -> None:
    license_file = tmp_path / "sample.lic"
    license_file.write_text(
        "\n".join(
            [
                "# comment",
                "FEATURE ANSYS-MECH vendor 1.0 2026-12-31 COUNT=2",
                "FEATURE ANSYS-CFD vendor 1.0 2027/01/15",
            ]
        ),
        encoding="utf-8",
    )

    parser = LicenseFeatureParser()
    rows = parser.parse(license_file)

    assert len(rows) == 2
    assert rows[0].feature_name == "ANSYS-MECH"
    assert rows[0].quantity == 2
    assert rows[0].expires_on == date(2026, 12, 31)
    assert rows[1].feature_name == "ANSYS-CFD"
    assert rows[1].expires_on == date(2027, 1, 15)


def test_parser_resolver_routes_by_provider_and_vendor(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    config = LicenseParserConfig(
        default_profile="default",
        profiles={
            "default": ParserProfileConfig(
                feature_keyword="FEATURE",
                feature_name_token_index=1,
                quantity_regexes=(r"\\bCOUNT=(\\d+)\\b",),
                expiry_regexes=(r"\\b(\\d{4}-\\d{2}-\\d{2})\\b",),
            ),
            "acme": ParserProfileConfig(
                feature_keyword="INCREMENT",
                feature_name_token_index=1,
                quantity_regexes=(r"\\bCOUNT=(\\d+)\\b",),
                expiry_regexes=(r"\\b(\\d{4}-\\d{2}-\\d{2})\\b",),
            ),
        },
        routes=(
            ParserRouteConfig(
                provider_pattern="CustomProvider", vendor_pattern="ACME*", profile="acme"
            ),
            ParserRouteConfig(provider_pattern="*", vendor_pattern="*", profile="default"),
        ),
    )

    def _fake_load() -> LicenseParserConfig:
        return config

    monkeypatch.setattr(
        "license_management.application.license_file_parser.load_license_parser_config",
        _fake_load,
    )

    target_file = tmp_path / "route.lic"
    target_file.write_text(
        "\n".join(
            [
                "FEATURE DEF-A vendor 1.0 2026-12-31 COUNT=1",
                "INCREMENT ACME-X vendor 1.0 2027-01-01 COUNT=2",
            ]
        ),
        encoding="utf-8",
    )

    resolver = LicenseParserResolver()

    default_rows = resolver.resolve(provider="Other", vendor="Other").parse(target_file)
    assert len(default_rows) == 1
    assert default_rows[0].feature_name == "DEF-A"

    acme_rows = resolver.resolve(provider="CustomProvider", vendor="ACME-TEAM").parse(target_file)
    assert len(acme_rows) == 1
    assert acme_rows[0].feature_name == "ACME-X"


def test_parser_supports_cadence_dd_mmm_yyyy_and_permanent(tmp_path: Path) -> None:
    target_file = tmp_path / "cadence.lic"
    target_file.write_text(
        "\n".join(
            [
                "FEATURE CADENCE_A cdslmd 1.0 31-mar-2026 1",
                "FEATURE CADENCE_B cdslmd 1.0 permanent 2",
            ]
        ),
        encoding="utf-8",
    )

    resolver = LicenseParserResolver()
    rows = resolver.resolve(provider="FlexNet", vendor="cadence").parse(target_file)

    assert len(rows) == 2
    assert rows[0].feature_name == "CADENCE_A"
    assert rows[0].expires_on == date(2026, 3, 31)
    assert rows[1].feature_name == "CADENCE_B"
    assert rows[1].expires_on == date(9999, 12, 31)


def test_parser_supports_siemens_increment_keyword(tmp_path: Path) -> None:
    target_file = tmp_path / "siemens_increment.lic"
    target_file.write_text(
        "\n".join(
            [
                "FEATURE IGNORE_THIS vendor 1.0 2026-12-31 COUNT=1",
                'INCREMENT ALPS_AS empyrean 1.0 30-apr-2026 300 SIGN="xxxx"',
            ]
        ),
        encoding="utf-8",
    )

    resolver = LicenseParserResolver()
    rows = resolver.resolve(provider="FlexNet", vendor="Siemens-EDA").parse(target_file)

    assert len(rows) == 2
    assert rows[0].feature_name == "IGNORE_THIS"
    assert rows[0].expires_on == date(2026, 12, 31)
    assert rows[0].quantity == 1
    assert rows[1].feature_name == "ALPS_AS"
    assert rows[1].expires_on == date(2026, 4, 30)
    assert rows[1].quantity == 300


def test_parser_increment_prefers_quantity_after_expiry_over_sign_tail(tmp_path: Path) -> None:
    target_file = tmp_path / "increment_with_sign_tail.lic"
    target_file.write_text(
        "INCREMENT XT_FEATURE empyrean 1.0 30-apr-2026 30 SIGN=ABCD 9999\n",
        encoding="utf-8",
    )

    resolver = LicenseParserResolver()
    rows = resolver.resolve(provider="FlexNet", vendor="Siemens-EDA").parse(target_file)

    assert len(rows) == 1
    assert rows[0].feature_name == "XT_FEATURE"
    assert rows[0].expires_on == date(2026, 4, 30)
    assert rows[0].quantity == 30


def test_parser_supports_empyrean_increment_route(tmp_path: Path) -> None:
    target_file = tmp_path / "empyrean_increment.lic"
    target_file.write_text(
        "INCREMENT ALPS_AS empyrean 1.0 30-apr-2026 300 SIGN=ABCD 9999\n",
        encoding="utf-8",
    )

    resolver = LicenseParserResolver()
    rows = resolver.resolve(provider="FlexNet", vendor="empyrean").parse(target_file)

    assert len(rows) == 1
    assert rows[0].feature_name == "ALPS_AS"
    assert rows[0].expires_on == date(2026, 4, 30)
    assert rows[0].quantity == 300


def test_parser_supports_mixed_feature_and_increment_for_same_vendor(tmp_path: Path) -> None:
    target_file = tmp_path / "mixed_vendor.lic"
    target_file.write_text(
        "\n".join(
            [
                "FEATURE FEAT_A empyrean 1.0 2026-12-31 COUNT=2",
                "INCREMENT FEAT_B empyrean 1.0 30-apr-2026 30 SIGN=ABCD 9999",
            ]
        ),
        encoding="utf-8",
    )

    resolver = LicenseParserResolver()
    rows = resolver.resolve(provider="FlexNet", vendor="empyrean").parse(target_file)

    assert len(rows) == 2
    assert rows[0].feature_name == "FEAT_A"
    assert rows[0].quantity == 2
    assert rows[1].feature_name == "FEAT_B"
    assert rows[1].expires_on == date(2026, 4, 30)
    assert rows[1].quantity == 30
