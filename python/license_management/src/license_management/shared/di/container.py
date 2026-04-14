"""Dependency injection container for the license management system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from license_management.adapters.flexnet_adapter import FlexNetAdapter
from license_management.adapters.provider_adapter import SshCommandExecutor
from license_management.application.import_pipeline import ImportPipelineService
from license_management.application.license_feature_catalog import LicenseFeatureCatalogService
from license_management.application.parsing.interfaces import (
    ParserProfileProtocol,
    ParserRouteProtocol,
)
from license_management.application.remote_license_file_service import RemoteLicenseFileService
from license_management.application.record_check_service import RecordCheckService
from license_management.domain.ports.license_repository import LicenseRepository
from license_management.infrastructure.repositories.sqlite_license_feature_repository import (
    SqliteLicenseFeatureRepository,
)
from license_management.shared.config.factory import (
    DefaultTableConfigFactory as SharedDefaultTableConfigFactory,
)
from license_management.shared.config.interfaces import (
    SshCredentialsProtocol,
    TableConfigFactory,
    TableConfigProtocol,
)


class RepositoryFactory(Protocol):
    """Factory for creating repository instances."""

    def create_license_repository(self, db_path: Path) -> LicenseRepository: ...

    def create_feature_repository(self, db_path: Path) -> object: ...


class CredentialsFactory(Protocol):
    """Factory for loading SSH credentials."""

    def load_credentials(self, project_root: Path) -> SshCredentialsProtocol: ...


class SshExecutorFactory(Protocol):
    """Factory for creating SSH executor instances."""

    def create_executor(self) -> SshCommandExecutor: ...


class AdapterFactory(Protocol):
    """Factory for creating provider adapter instances."""

    def create_flexnet_adapter(self, executor: SshCommandExecutor) -> FlexNetAdapter: ...


class ServiceFactory(Protocol):
    """Factory for creating application services."""

    def create_import_service(
        self,
        repository: LicenseRepository,
        feature_catalog: LicenseFeatureCatalogService | None = None,
        table_config: TableConfigProtocol | None = None,
    ) -> ImportPipelineService: ...

    def create_feature_catalog(
        self,
        feature_repository: object,
        ssh_executor: SshCommandExecutor,
        ssh_username: str,
        ssh_password: str | None,
        parser_route_config: ParserRouteProtocol | None = None,
        parser_profile_config: ParserProfileProtocol | None = None,
    ) -> LicenseFeatureCatalogService: ...

    def create_record_checker(
        self,
        ssh_executor: SshCommandExecutor,
        ssh_username: str,
        ssh_password: str | None,
    ) -> RecordCheckService: ...

    def create_remote_license_service(
        self, executor: SshCommandExecutor
    ) -> RemoteLicenseFileService: ...


@dataclass(slots=True)
class ServiceContainer:
    """Container for application services and dependencies."""

    repository: LicenseRepository
    feature_catalog: LicenseFeatureCatalogService
    checker: RecordCheckService
    ssh_executor: SshCommandExecutor
    remote_license_service: RemoteLicenseFileService
    ssh_credentials: SshCredentialsProtocol
    feedback: Any
    view_model: Any
    search: Any
    binder: Any
    table_config: TableConfigProtocol


class DefaultServiceContainerBuilder:
    """Default implementation of service container builder."""

    def __init__(
        self,
        *,
        repository_factory: RepositoryFactory | None = None,
        credentials_factory: CredentialsFactory | None = None,
        ssh_executor_factory: SshExecutorFactory | None = None,
        adapter_factory: AdapterFactory | None = None,
        service_factory: ServiceFactory | None = None,
        table_config_factory: TableConfigFactory | None = None,
    ) -> None:
        self._repository_factory = repository_factory or DefaultRepositoryFactory()
        self._credentials_factory = credentials_factory or DefaultCredentialsFactory()
        self._ssh_executor_factory = ssh_executor_factory or DefaultSshExecutorFactory()
        self._adapter_factory = adapter_factory or DefaultAdapterFactory()
        self._service_factory = service_factory or DefaultServiceFactory()
        self._table_config_factory = table_config_factory or DefaultTableConfigFactory()

    def build(self, project_root: Path | None = None) -> ServiceContainer:
        """Build a fully configured service container."""
        if project_root is None:
            project_root = Path(__file__).resolve().parents[3]

        db_path = project_root / "data" / "license_management.sqlite3"
        feature_db_path = project_root / "data" / "license_feature_catalog.sqlite3"

        repository = self._repository_factory.create_license_repository(db_path)
        feature_repository = self._repository_factory.create_feature_repository(feature_db_path)
        ssh_credentials = self._credentials_factory.load_credentials(project_root)
        ssh_executor = self._ssh_executor_factory.create_executor()
        table_config = self._table_config_factory.create_table_config()

        from license_management.application.parsing.factory import DefaultParserConfigFactory
        from license_management.application.compare_service import CrossTargetCompareService
        from license_management.gui.flows.dialog_flows import DialogFlowBinder
        from license_management.gui.feature_search import FeatureSearchController
        from license_management.gui.state.models import FeedbackCenter
        from license_management.gui.state.view_model import MainListViewModel

        parser_factory = DefaultParserConfigFactory()

        feature_catalog = self._service_factory.create_feature_catalog(
            feature_repository=feature_repository,
            ssh_executor=ssh_executor,
            ssh_username=ssh_credentials.username,
            ssh_password=(ssh_credentials.password or None),
            parser_route_config=parser_factory.create_parser_route_config(),
            parser_profile_config=parser_factory.create_parser_profile_config(),
        )

        checker = self._service_factory.create_record_checker(
            ssh_executor=ssh_executor,
            ssh_username=ssh_credentials.username,
            ssh_password=(ssh_credentials.password or None),
        )

        remote_license_service = self._service_factory.create_remote_license_service(
            executor=ssh_executor
        )

        feedback = FeedbackCenter()
        view_model = MainListViewModel(warning_days=30, table_config=table_config)
        search = FeatureSearchController(view_model)

        import_service = self._service_factory.create_import_service(
            repository=repository,
            feature_catalog=feature_catalog,
            table_config=table_config,
        )

        flexnet_adapter = self._adapter_factory.create_flexnet_adapter(executor=ssh_executor)
        compare_service = CrossTargetCompareService()

        binder = DialogFlowBinder(
            repository=repository,
            feedback_center=feedback,
            import_service=import_service,
            feature_catalog_service=feature_catalog,
            flexnet_adapter=flexnet_adapter,
            compare_service=compare_service,
            table_config=table_config,
        )

        return ServiceContainer(
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
            table_config=table_config,
        )


class DefaultRepositoryFactory:
    """Default repository factory using SQLite implementations."""

    def create_license_repository(self, db_path: Path) -> LicenseRepository:
        from license_management.infrastructure.repositories.sqlite_license_repository import (
            SqliteLicenseRepository,
        )

        return SqliteLicenseRepository(db_path)

    def create_feature_repository(self, db_path: Path) -> object:
        from license_management.infrastructure.repositories.sqlite_license_feature_repository import (
            SqliteLicenseFeatureRepository,
        )

        return SqliteLicenseFeatureRepository(db_path)


class DefaultCredentialsFactory:
    """Default credentials factory loading from config files."""

    def load_credentials(self, project_root: Path) -> SshCredentialsProtocol:
        from license_management.shared.config.ssh_credentials_config import load_ssh_credentials

        return load_ssh_credentials(project_root)


class DefaultSshExecutorFactory:
    """Default SSH executor factory using OpenSSH implementation."""

    def create_executor(self) -> SshCommandExecutor:
        from license_management.adapters.ssh_command_executor import OpenSshCommandExecutor

        return OpenSshCommandExecutor()


class DefaultAdapterFactory:
    """Default adapter factory using FlexNet implementation."""

    def create_flexnet_adapter(self, executor: SshCommandExecutor) -> FlexNetAdapter:
        from license_management.adapters.flexnet_adapter import FlexNetAdapter

        return FlexNetAdapter(executor=executor)


class DefaultServiceFactory:
    """Default service factory."""

    def create_import_service(
        self,
        repository: LicenseRepository,
        feature_catalog: LicenseFeatureCatalogService | None = None,
        table_config: TableConfigProtocol | None = None,
    ) -> ImportPipelineService:
        return ImportPipelineService(
            repository,
            feature_catalog_service=feature_catalog,
            table_config=table_config,
        )

    def create_feature_catalog(
        self,
        feature_repository: object,
        ssh_executor: SshCommandExecutor,
        ssh_username: str,
        ssh_password: str | None,
        parser_route_config: ParserRouteProtocol | None = None,
        parser_profile_config: ParserProfileProtocol | None = None,
    ) -> LicenseFeatureCatalogService:
        return LicenseFeatureCatalogService(
            repository=cast(SqliteLicenseFeatureRepository, feature_repository),
            ssh_executor=ssh_executor,
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            parser_route_config=parser_route_config,
            parser_profile_config=parser_profile_config,
        )

    def create_record_checker(
        self,
        ssh_executor: SshCommandExecutor,
        ssh_username: str,
        ssh_password: str | None,
    ) -> RecordCheckService:
        return RecordCheckService(
            ssh_executor=ssh_executor,
            ssh_username=ssh_username,
            ssh_password=ssh_password,
        )

    def create_remote_license_service(
        self, executor: SshCommandExecutor
    ) -> RemoteLicenseFileService:
        return RemoteLicenseFileService(executor=executor)


class DefaultTableConfigFactory(TableConfigFactory):
    """Default table configuration factory."""

    def create_table_config(self) -> TableConfigProtocol:
        return SharedDefaultTableConfigFactory().create_table_config()
