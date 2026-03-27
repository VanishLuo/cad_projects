from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

from license_management.domain.models.license_record import LicenseRecord
from license_management.infrastructure.config.license_parser_config import (
    ParserProfileConfig,
    ParserRouteConfig,
    load_license_parser_config,
)
from license_management.shared.path_normalization import normalize_local_path_text


@dataclass(slots=True, frozen=True)
class ParsedLicenseFeature:
    feature_name: str
    expires_on: date
    quantity: int = 1


class FeatureLineMatcher(Protocol):
    def matches(self, line: str) -> bool: ...


class FeatureNameExtractor(Protocol):
    def extract(self, line: str, tokens: list[str]) -> str | None: ...


class FeatureQuantityExtractor(Protocol):
    def extract(self, line: str, tokens: list[str]) -> int | None: ...


class FeatureExpiryExtractor(Protocol):
    def extract(self, line: str, tokens: list[str]) -> date | None: ...


class ParsedFeatureParser(Protocol):
    def parse(self, file_path: Path) -> list[ParsedLicenseFeature]: ...

    def parse_text(self, content: str) -> list[ParsedLicenseFeature]: ...


class DefaultFeatureLineMatcher:
    def matches(self, line: str) -> bool:
        return line.lstrip().upper().startswith("FEATURE ")


class DefaultFeatureNameExtractor:
    def extract(self, line: str, tokens: list[str]) -> str | None:
        _ = line
        if len(tokens) < 2:
            return None
        return tokens[1].strip() or None


class DefaultFeatureQuantityExtractor:
    _quantity_regex = re.compile(r"\b(?:COUNT|QTY|QUANTITY)\s*=\s*(\d+)\b", re.IGNORECASE)

    def extract(self, line: str, tokens: list[str]) -> int | None:
        match = self._quantity_regex.search(line)
        if match is not None:
            return max(1, int(match.group(1)))

        for token in reversed(tokens):
            if token.isdigit():
                return max(1, int(token))
        return None


class DefaultFeatureExpiryExtractor:
    _iso_regex = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
    _slash_regex = re.compile(r"\b(\d{4}/\d{2}/\d{2})\b")

    def extract(self, line: str, tokens: list[str]) -> date | None:
        _ = tokens
        match = self._iso_regex.search(line)
        if match is not None:
            try:
                return date.fromisoformat(match.group(1))
            except ValueError:
                pass

        slash_match = self._slash_regex.search(line)
        if slash_match is not None:
            try:
                return date.fromisoformat(slash_match.group(1).replace("/", "-"))
            except ValueError:
                pass

        return None


class ConfigurableFeatureParser:
    """Parses license files with profile-driven extraction rules."""

    def __init__(self, profile: ParserProfileConfig) -> None:
        self._feature_keyword = profile.feature_keyword.upper()
        self._feature_name_token_index = max(0, profile.feature_name_token_index)
        self._quantity_regexes = [re.compile(item, re.IGNORECASE) for item in profile.quantity_regexes]
        self._expiry_regexes = [re.compile(item, re.IGNORECASE) for item in profile.expiry_regexes]
        self._cadence_date_regex = re.compile(r"\b(\d{1,2})-([A-Za-z]{3})-(\d{4})\b")
        self._permanent_regex = re.compile(r"\b(permanent|perpetual)\b", re.IGNORECASE)

    def parse(self, file_path: Path) -> list[ParsedLicenseFeature]:
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(str(file_path))

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return self.parse_text(content)

    def parse_text(self, content: str) -> list[ParsedLicenseFeature]:
        features: list[ParsedLicenseFeature] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            tokens = [token for token in line.split() if token]
            if not tokens:
                continue
            if tokens[0].upper() != self._feature_keyword:
                continue

            if len(tokens) <= self._feature_name_token_index:
                continue
            feature_name = tokens[self._feature_name_token_index].strip()
            if feature_name == "":
                continue

            quantity = self._extract_quantity(line=line, tokens=tokens) or 1
            expires_on = self._extract_expiry(line=line) or date.today()
            features.append(
                ParsedLicenseFeature(
                    feature_name=feature_name,
                    expires_on=expires_on,
                    quantity=max(1, quantity),
                )
            )
        return features

    def _extract_quantity(self, *, line: str, tokens: list[str]) -> int | None:
        for quantity_regex in self._quantity_regexes:
            match = quantity_regex.search(line)
            if match is None:
                continue
            try:
                return max(1, int(match.group(1)))
            except (TypeError, ValueError, IndexError):
                continue

        for token in reversed(tokens):
            if token.isdigit():
                return max(1, int(token))
        return None

    def _extract_expiry(self, *, line: str) -> date | None:
        for expiry_regex in self._expiry_regexes:
            match = expiry_regex.search(line)
            if match is None:
                continue
            raw_date = match.group(1)
            try:
                return date.fromisoformat(raw_date.replace("/", "-"))
            except ValueError:
                parsed = self._parse_cadence_date(raw_date)
                if parsed is not None:
                    return parsed
                continue

        cadence_match = self._cadence_date_regex.search(line)
        if cadence_match is not None:
            day = cadence_match.group(1)
            month = cadence_match.group(2)
            year = cadence_match.group(3)
            parsed = self._parse_cadence_date(f"{day}-{month}-{year}")
            if parsed is not None:
                return parsed

        if self._permanent_regex.search(line) is not None:
            # Keep permanent features always active in expiration status engine.
            return date(9999, 12, 31)

        return None

    def _parse_cadence_date(self, raw_text: str) -> date | None:
        parts = raw_text.strip().split("-")
        if len(parts) != 3:
            return None
        day_text, month_text, year_text = parts
        month_map = {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }
        month = month_map.get(month_text.lower())
        if month is None:
            return None
        try:
            return date(int(year_text), month, int(day_text))
        except ValueError:
            return None


class LicenseParserResolver:
    """Resolves parser profiles according to provider/vendor routing rules."""

    def __init__(self) -> None:
        self._config = load_license_parser_config()
        self._cache: dict[str, ConfigurableFeatureParser] = {}

    def resolve(self, *, provider: str, vendor: str) -> ConfigurableFeatureParser:
        profile_name = self._select_profile_name(provider=provider, vendor=vendor)
        parser = self._cache.get(profile_name)
        if parser is None:
            profile = self._config.profiles[profile_name]
            parser = ConfigurableFeatureParser(profile)
            self._cache[profile_name] = parser
        return parser

    def _select_profile_name(self, *, provider: str, vendor: str) -> str:
        provider_text = provider.strip()
        vendor_text = vendor.strip()
        for route in self._config.routes:
            if _route_matches(route, provider=provider_text, vendor=vendor_text):
                return route.profile
        return self._config.default_profile


def _route_matches(route: ParserRouteConfig, *, provider: str, vendor: str) -> bool:
    return fnmatch.fnmatch(provider.lower(), route.provider_pattern.lower()) and fnmatch.fnmatch(
        vendor.lower(), route.vendor_pattern.lower()
    )


class LicenseFeatureParser:
    """Backward-compatible parser facade using default resolver routing."""

    def __init__(
        self,
        *,
        line_matcher: FeatureLineMatcher | None = None,
        name_extractor: FeatureNameExtractor | None = None,
        quantity_extractor: FeatureQuantityExtractor | None = None,
        expiry_extractor: FeatureExpiryExtractor | None = None,
    ) -> None:
        _ = (line_matcher, name_extractor, quantity_extractor, expiry_extractor)
        self._resolver = LicenseParserResolver()

    def parse(self, file_path: Path) -> list[ParsedLicenseFeature]:
        parser = self._resolver.resolve(provider="", vendor="")
        return parser.parse(file_path)

    def parse_text(self, content: str) -> list[ParsedLicenseFeature]:
        parser = self._resolver.resolve(provider="", vendor="")
        return parser.parse_text(content)


class LicenseRecordExpander:
    """Expands a base record into feature-level records based on its license file path."""

    def __init__(
        self,
        parser: ParsedFeatureParser | None = None,
        resolver: LicenseParserResolver | None = None,
    ) -> None:
        self._parser = parser
        self._resolver = resolver or LicenseParserResolver()

    def expand_from_record(self, record: LicenseRecord) -> list[LicenseRecord]:
        path = normalize_local_path_text(record.license_file_path)
        if path == "":
            return [record]

        selected_parser = self._parser
        if selected_parser is None:
            selected_parser = self._resolver.resolve(provider=record.provider, vendor=record.vendor)

        parsed_features = selected_parser.parse(Path(path))
        if not parsed_features:
            return [record]

        expanded: list[LicenseRecord] = []
        for feature_index, parsed in enumerate(parsed_features, start=1):
            for quantity_index in range(parsed.quantity):
                suffix = (
                    f"#{feature_index}"
                    if parsed.quantity == 1
                    else f"#{feature_index}-{quantity_index + 1}"
                )
                expanded.append(
                    LicenseRecord(
                        record_id=f"{record.record_id}{suffix}",
                        server_name=record.server_name,
                        provider=record.provider,
                        prot=record.prot,
                        feature_name=parsed.feature_name,
                        process_name=record.process_name,
                        expires_on=parsed.expires_on,
                        vendor=record.vendor,
                        start_executable_path=record.start_executable_path,
                        license_file_path=record.license_file_path,
                        start_option_override=record.start_option_override,
                    )
                )

        if len(expanded) == 1:
            only = expanded[0]
            expanded[0] = LicenseRecord(
                record_id=record.record_id,
                server_name=only.server_name,
                provider=only.provider,
                prot=only.prot,
                feature_name=only.feature_name,
                process_name=only.process_name,
                expires_on=only.expires_on,
                vendor=only.vendor,
                start_executable_path=only.start_executable_path,
                license_file_path=only.license_file_path,
                start_option_override=only.start_option_override,
            )

        return expanded
