"""Application service exports."""

from importlib import import_module

__all__ = [
    "CompareIssue",
    "CompareReport",
    "CatalogSyncResult",
    "CrossTargetCompareService",
    "ExpirationState",
    "ExpirationStateEngine",
    "ExpirationStatus",
    "ImportPipelineService",
    "ImportReport",
    "LicenseFeatureCatalogService",
    "LicenseFeatureParser",
    "LicenseParserResolver",
    "LicenseRecordExpander",
    "ParsedLicenseFeature",
    "RecordCheckIssue",
    "RecordCheckService",
    "TargetSnapshot",
]

_EXPORTS = {
    "CompareIssue": ".compare_service",
    "CompareReport": ".compare_service",
    "CrossTargetCompareService": ".compare_service",
    "TargetSnapshot": ".compare_service",
    "ExpirationState": "license_management.domain.expiration_engine",
    "ExpirationStateEngine": "license_management.domain.expiration_engine",
    "ExpirationStatus": "license_management.domain.expiration_engine",
    "ImportPipelineService": ".import_pipeline",
    "ImportReport": ".import_pipeline",
    "CatalogSyncResult": ".license_feature_catalog",
    "LicenseFeatureCatalogService": ".license_feature_catalog",
    "LicenseFeatureParser": ".license_file_parser",
    "LicenseParserResolver": ".license_file_parser",
    "LicenseRecordExpander": ".license_file_parser",
    "ParsedLicenseFeature": ".license_file_parser",
    "RecordCheckIssue": ".record_check_service",
    "RecordCheckService": ".record_check_service",
}


def __getattr__(name: str) -> object:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    if module_name.startswith("."):
        module = import_module(module_name, __name__)
    else:
        module = import_module(module_name)
    return getattr(module, name)
