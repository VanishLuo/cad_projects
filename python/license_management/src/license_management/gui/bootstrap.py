from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from license_management.adapters.flexnet_adapter import FlexNetAdapter
from license_management.adapters.provider_adapter import SshCommandExecutor
from license_management.adapters.ssh_command_executor import OpenSshCommandExecutor
from license_management.application.compare_service import CrossTargetCompareService
from license_management.application.import_pipeline import ImportPipelineService
from license_management.application.license_feature_catalog import LicenseFeatureCatalogService
from license_management.application.remote_license_file_service import RemoteLicenseFileService
from license_management.application.record_check_service import RecordCheckService
from license_management.gui.flows.dialog_flows import DialogFlowBinder
from license_management.gui.feature_search import FeatureSearchController
from license_management.gui.main_window import MainWindow, UiLicenseRepositoryProtocol
from license_management.gui.state.models import FeedbackCenter
from license_management.gui.qt_compat import QApplication, QFont, QFontDatabase, app_exec
from license_management.gui.state.view_model import MainListViewModel
from license_management.infrastructure.config.ssh_credentials_config import (
    SshCredentials,
    load_ssh_credentials,
)
from license_management.infrastructure.repositories.sqlite_license_feature_repository import (
    SqliteLicenseFeatureRepository,
)
from license_management.infrastructure.repositories.sqlite_license_repository import (
    SqliteLicenseRepository,
)


@dataclass(slots=True)
class UiContext:
    repository: UiLicenseRepositoryProtocol
    feature_catalog: LicenseFeatureCatalogService
    checker: RecordCheckService
    ssh_executor: SshCommandExecutor
    remote_license_service: RemoteLicenseFileService
    ssh_credentials: SshCredentials
    feedback: FeedbackCenter
    view_model: MainListViewModel
    search: FeatureSearchController
    binder: DialogFlowBinder


def build_context() -> UiContext:
    project_root = Path(__file__).resolve().parents[3]
    db_path = project_root / "data" / "license_management.sqlite3"
    feature_db_path = project_root / "data" / "license_feature_catalog.sqlite3"
    repository = SqliteLicenseRepository(db_path)
    ssh_credentials = load_ssh_credentials(project_root)
    ssh_executor: SshCommandExecutor = OpenSshCommandExecutor()
    feature_repository = SqliteLicenseFeatureRepository(feature_db_path)
    feature_catalog = LicenseFeatureCatalogService(
        repository=feature_repository,
        ssh_executor=ssh_executor,
        ssh_username=ssh_credentials.username,
        ssh_password=(ssh_credentials.password or None),
    )
    checker = RecordCheckService(
        ssh_executor=ssh_executor,
        ssh_username=ssh_credentials.username,
        ssh_password=(ssh_credentials.password or None),
    )
    remote_license_service = RemoteLicenseFileService(executor=ssh_executor)
    feedback = FeedbackCenter()
    view_model = MainListViewModel(warning_days=30)
    search = FeatureSearchController(view_model)
    import_service = ImportPipelineService(repository, feature_catalog_service=feature_catalog)
    compare_service = CrossTargetCompareService()
    flexnet = FlexNetAdapter(
        executor=ssh_executor,
    )
    binder = DialogFlowBinder(
        repository=repository,
        feedback_center=feedback,
        import_service=import_service,
        feature_catalog_service=feature_catalog,
        flexnet_adapter=flexnet,
        compare_service=compare_service,
    )
    return UiContext(
        repository=repository,
        feature_catalog=feature_catalog,
        checker=checker,
        ssh_executor=ssh_executor,
        remote_license_service=remote_license_service,
        ssh_credentials=ssh_credentials,
        feedback=feedback,
        view_model=view_model,
        search=search,
        binder=binder,
    )


def run_gui() -> int:
    app = QApplication.instance()
    if app is None or not isinstance(app, QApplication):
        app = QApplication([])
    _apply_preferred_font(app)
    _apply_stylesheet(app)
    window = MainWindow(build_context())
    window.show()
    return app_exec(app)


def _apply_preferred_font(app: QApplication) -> None:
    preferred_families = [
        "SF Pro Text",
        "PingFang SC",
        "PingFang HK",
        "Helvetica Neue",
        "San Francisco",
        "Segoe UI Variable",
        "Microsoft YaHei UI",
    ]
    available_families = {name.lower(): name for name in QFontDatabase().families()}

    selected_family: str | None = None
    for family in preferred_families:
        if family.lower() in available_families:
            selected_family = available_families[family.lower()]
            break

    if selected_family is None:
        return

    font = QFont(selected_family)
    app.setFont(font)


def _apply_stylesheet(app: QApplication) -> None:
    style_path = Path(__file__).with_name("app.qss")
    try:
        stylesheet = style_path.read_text(encoding="utf-8")
    except OSError:
        return

    app.setStyleSheet(stylesheet)
