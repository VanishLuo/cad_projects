"""Repository implementations."""

from importlib import import_module

__all__ = [
    "InMemoryLicenseRepository",
    "SqliteLicenseFeatureRepository",
    "SqliteLicenseRepository",
    "SqliteLicenseTextSnapshotRepository",
]

_EXPORTS = {
    "InMemoryLicenseRepository": ".in_memory_license_repository",
    "SqliteLicenseFeatureRepository": ".sqlite_license_feature_repository",
    "SqliteLicenseRepository": ".sqlite_license_repository",
    "SqliteLicenseTextSnapshotRepository": ".sqlite_license_text_snapshot_repository",
}


def __getattr__(name: str) -> object:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    return getattr(module, name)
