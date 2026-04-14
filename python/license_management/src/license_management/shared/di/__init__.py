"""Dependency injection module for clean architecture.

English:
Provides dependency injection abstractions to decouple upper layers
(GUI, Application) from infrastructure implementations.

Chinese:
提供依赖注入抽象以解耦上层（GUI、应用）与基础设施实现。
"""

from license_management.shared.di.container import (
    DefaultServiceContainerBuilder,
    DefaultAdapterFactory,
    DefaultCredentialsFactory,
    DefaultRepositoryFactory,
    DefaultServiceFactory,
    DefaultSshExecutorFactory,
    SshCredentialsProtocol,
    RepositoryFactory,
    CredentialsFactory,
    SshExecutorFactory,
    AdapterFactory,
    ServiceFactory,
    ServiceContainer,
)

__all__ = [
    "ServiceContainer",
    "SshCredentialsProtocol",
    "RepositoryFactory",
    "CredentialsFactory",
    "SshExecutorFactory",
    "AdapterFactory",
    "ServiceFactory",
    "DefaultServiceContainerBuilder",
    "DefaultRepositoryFactory",
    "DefaultCredentialsFactory",
    "DefaultSshExecutorFactory",
    "DefaultAdapterFactory",
    "DefaultServiceFactory",
]
