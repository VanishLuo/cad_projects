"""GUI interaction layer exports."""

from license_management.gui.controllers.compare_text_controller import (
    CompareTextController,
    CompareTextPayload,
)
from license_management.gui.check.check_completion_coordinator import CheckCompletionCoordinator
from license_management.gui.check.check_publish_handler import CheckPublishHandler
from license_management.gui.composition.main_window_action_handlers import (
    MainWindowActionHandlers,
    MainWindowActionHooks,
)
from license_management.gui.composition.main_window_layout_builder import (
    MainWindowLayoutBuilder,
    MainWindowLayoutResult,
)
from license_management.gui.composition.main_window_table_helper import MainWindowTableHelper
from license_management.gui.flows.dialog_flows import DialogFlowBinder, DialogResult
from license_management.gui.feature_search import FeatureSearchController, FeatureSearchResult
from license_management.gui.state.models import FeedbackCenter, FeedbackMessage, UiLicenseRow
from license_management.gui.validation_feedback import (
    ValidationIssue,
    ValidationResult,
    to_license_record,
    validate_license_form,
)
from license_management.gui.state.view_model import MainListViewModel, SearchFilters

__all__ = [
    "CompareTextController",
    "CompareTextPayload",
    "CheckCompletionCoordinator",
    "CheckPublishHandler",
    "DialogFlowBinder",
    "DialogResult",
    "FeatureSearchController",
    "FeatureSearchResult",
    "FeedbackCenter",
    "FeedbackMessage",
    "MainWindowActionHandlers",
    "MainWindowActionHooks",
    "MainWindowLayoutBuilder",
    "MainWindowLayoutResult",
    "MainWindowTableHelper",
    "MainListViewModel",
    "SearchFilters",
    "UiLicenseRow",
    "ValidationIssue",
    "ValidationResult",
    "to_license_record",
    "validate_license_form",
]
