"""GUI interaction layer exports."""

from license_management.gui.dialog_flows import DialogFlowBinder, DialogResult
from license_management.gui.feature_search import FeatureSearchController, FeatureSearchResult
from license_management.gui.models import FeedbackCenter, FeedbackMessage, UiLicenseRow
from license_management.gui.validation_feedback import (
    ValidationIssue,
    ValidationResult,
    to_license_record,
    validate_license_form,
)
from license_management.gui.view_model import MainListViewModel, SearchFilters

__all__ = [
    "DialogFlowBinder",
    "DialogResult",
    "FeatureSearchController",
    "FeatureSearchResult",
    "FeedbackCenter",
    "FeedbackMessage",
    "MainListViewModel",
    "SearchFilters",
    "UiLicenseRow",
    "ValidationIssue",
    "ValidationResult",
    "to_license_record",
    "validate_license_form",
]
