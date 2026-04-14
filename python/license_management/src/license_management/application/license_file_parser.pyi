"""Type stubs for license_file_parser.

This file provides type hints while maintaining clean architecture boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from license_management.infrastructure.config.license_parser_config import (
    LicenseParserConfig,
)
from license_management.application.parsing.interfaces import (
    ParserProfileProtocol,
    ParserRouteProtocol,
)

@dataclass(slots=True, frozen=True)
class ParsedLicenseFeature:
    feature_name: str
    expires_on: date
    quantity: int = 1

def load_license_parser_config() -> LicenseParserConfig: ...

class LicenseFeatureParser:
    def __init__(self, profile: object | None = None) -> None: ...
    def parse(self, file_path: Path) -> list[ParsedLicenseFeature]: ...
    def parse_text(self, content: str) -> list[ParsedLicenseFeature]: ...

class LicenseParserResolver:
    def __init__(self, config: LicenseParserConfig | None = None) -> None: ...
    def resolve(self, *, provider: str, vendor: str) -> LicenseFeatureParser: ...

class LicenseFeatureParserService:
    def __init__(
        self,
        *,
        parser_route_config: ParserRouteProtocol,
        parser_profile_config: ParserProfileProtocol,
    ) -> None: ...
    def parse_features(
        self,
        _record_id: str,
        provider: str,
        vendor: str,
        license_file_path: str,
    ) -> list[ParsedLicenseFeature]: ...
    def parse_text(
        self,
        content: str,
        *,
        provider: str = "*",
        vendor: str = "*",
    ) -> list[ParsedLicenseFeature]: ...

class LicenseRecordExpander:
    def __init__(self, resolver: LicenseParserResolver | None = None) -> None: ...
    def expand_features(
        self,
        *,
        provider: str,
        vendor: str,
        license_file_path: str,
    ) -> list[ParsedLicenseFeature]: ...
