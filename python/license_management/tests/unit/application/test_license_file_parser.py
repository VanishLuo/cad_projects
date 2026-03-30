from __future__ import annotations

from datetime import date
from pathlib import Path
from pytest import MonkeyPatch

from license_management.application.license_file_parser import (
    LicenseParserResolver,
    LicenseFeatureParser,
    LicenseRecordExpander,
)
from license_management.infrastructure.config.license_parser_config import (
    LicenseParserConfig,
    ParserProfileConfig,
    ParserRouteConfig,
)
from license_management.domain.models.license_record import LicenseRecord


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


def test_license_record_expander_splits_rows_by_feature_quantity(tmp_path: Path) -> None:
    license_file = tmp_path / "sample.lic"
    license_file.write_text(
        "FEATURE FEAT-A vendor 1.0 2026-12-31 COUNT=2\n",
        encoding="utf-8",
    )
    base = LicenseRecord(
        record_id="base",
        server_name="srv-a",
        provider="FlexNet",
        prot="27000",
        feature_name="",
        process_name="lmgrd",
        expires_on=date(2026, 1, 1),
        license_file_path=str(license_file),
    )

    expander = LicenseRecordExpander()
    expanded = expander.expand_from_record(base)

    assert len(expanded) == 2
    assert expanded[0].record_id == "base#1-1"
    assert expanded[1].record_id == "base#1-2"
    assert all(item.feature_name == "FEAT-A" for item in expanded)
    assert all(item.expires_on == date(2026, 12, 31) for item in expanded)


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

    assert len(rows) == 1
    assert rows[0].feature_name == "ALPS_AS"
    assert rows[0].expires_on == date(2026, 4, 30)
    assert rows[0].quantity == 300
