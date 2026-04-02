"""Tests for capacity policy management system."""

from __future__ import annotations

import time
import pytest

from license_management.shared.policies import (
    CapacityPolicyEnforcer,
    CapacityPolicyConfig,
    CapacityMetrics,
    CapacityState,
    create_capacity_policy,
)


class TestCapacityMetrics:
    """Test CapacityMetrics functionality."""

    def test_utilization_rate_calculation(self) -> None:
        """Test utilization rate calculation."""
        metrics = CapacityMetrics(
            current_load=10,
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={"cpu": 50.0}
        )

        assert metrics.utilization_rate == 0.5

    def test_utilization_rate_zero_capacity(self) -> None:
        """Test utilization rate with zero max capacity."""
        metrics = CapacityMetrics(
            current_load=10,
            max_capacity=0,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        assert metrics.utilization_rate == 0.0

    def test_capacity_state_normal(self) -> None:
        """Test normal capacity state."""
        metrics = CapacityMetrics(
            current_load=10,
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        assert metrics.state == CapacityState.NORMAL

    def test_capacity_state_warning(self) -> None:
        """Test warning capacity state."""
        metrics = CapacityMetrics(
            current_load=17,  # 85% utilization
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        assert metrics.state == CapacityState.WARNING

    def test_capacity_state_critical(self) -> None:
        """Test critical capacity state."""
        metrics = CapacityMetrics(
            current_load=19,  # 95% utilization
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        assert metrics.state == CapacityState.CRITICAL

    def test_capacity_state_overloaded(self) -> None:
        """Test overloaded capacity state."""
        metrics = CapacityMetrics(
            current_load=21,  # 105% utilization
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        assert metrics.state == CapacityState.OVERLOADED

    def test_can_accept_load_normal_state(self) -> None:
        """Test load acceptance in normal state."""
        metrics = CapacityMetrics(
            current_load=10,
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        assert metrics.can_accept_load(5)
        assert not metrics.can_accept_load(15)

    def test_can_accept_load_critical_state(self) -> None:
        """Test load acceptance in critical state."""
        metrics = CapacityMetrics(
            current_load=19,
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        assert metrics.can_accept_load(1)
        assert not metrics.can_accept_load(2)


class TestCapacityPolicyEnforcer:
    """Test CapacityPolicyEnforcer functionality."""

    def test_policy_creation(self) -> None:
        """Test policy enforcer creation."""
        config = CapacityPolicyConfig()
        enforcer = CapacityPolicyEnforcer(config)

        assert enforcer.config == config
        assert enforcer.current_capacity == config.base_capacity
        assert len(enforcer.metrics_history) == 0
        assert enforcer.last_expansion_time is None

    def test_metrics_recording(self) -> None:
        """Test metrics recording."""
        config = CapacityPolicyConfig()
        enforcer = CapacityPolicyEnforcer(config)

        metrics = CapacityMetrics(
            current_load=10,
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        enforcer.record_metrics(metrics)

        assert len(enforcer.metrics_history) == 1
        assert enforcer.get_current_metrics() == metrics

    def test_capacity_request_approval_no_metrics(self) -> None:
        """Test capacity request when no metrics available."""
        config = CapacityPolicyConfig()
        enforcer = CapacityPolicyEnforcer(config)

        result = enforcer.evaluate_capacity_request(5)

        assert result["approved"]
        assert "No metrics available" in result["reason"]

    def test_capacity_request_approval_sufficient_capacity(self) -> None:
        """Test capacity request approval with sufficient capacity."""
        config = CapacityPolicyConfig()
        enforcer = CapacityPolicyEnforcer(config)

        metrics = CapacityMetrics(
            current_load=10,
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        enforcer.record_metrics(metrics)
        result = enforcer.evaluate_capacity_request(5)

        assert result["approved"]
        assert "Capacity available" in result["reason"]
        assert result["remaining_capacity"] == 5

    def test_capacity_request_rejection_insufficient_capacity(self) -> None:
        """Test capacity request rejection with insufficient capacity."""
        config = CapacityPolicyConfig(
            max_expansion_factor=1.0  # No expansion allowed
        )
        enforcer = CapacityPolicyEnforcer(config)

        metrics = CapacityMetrics(
            current_load=18,
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        enforcer.record_metrics(metrics)
        result = enforcer.evaluate_capacity_request(5)

        # Should reject because no expansion possible (max_expansion_factor=1.0)
        assert not result["approved"]
        assert "System at capacity" in result["reason"]

    def test_capacity_expansion_in_warning_state(self) -> None:
        """Test capacity expansion in warning state."""
        config = CapacityPolicyConfig()
        enforcer = CapacityPolicyEnforcer(config)

        # Use a smaller request to trigger warning but not overload
        metrics = CapacityMetrics(
            current_load=15,  # 75% utilization - still normal
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        enforcer.record_metrics(metrics)
        # Request that pushes into warning state (15+6=21 > 20)
        result = enforcer.evaluate_capacity_request(6)

        # Should approve and expand
        assert result["approved"]
        assert "Capacity expanded" in result["reason"]
        assert result["previous_capacity"] == 20
        assert result["new_capacity"] > 20
        assert enforcer.current_capacity > 20

    def test_capacity_report_generation(self) -> None:
        """Test capacity report generation."""
        config = CapacityPolicyConfig()
        enforcer = CapacityPolicyEnforcer(config)

        metrics = CapacityMetrics(
            current_load=10,
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={"cpu": 50.0, "memory": 40.0}
        )

        enforcer.record_metrics(metrics)
        report = enforcer.get_capacity_report()

        assert "timestamp" in report
        assert "current_capacity" in report
        assert "base_capacity" in report
        assert "state" in report
        assert "utilization_rate" in report
        assert report["current_capacity"] == 20
        assert report["utilization_rate"] == 0.5

    def test_metrics_cleanup_old_records(self) -> None:
        """Test old metrics cleanup."""
        config = CapacityPolicyConfig(metrics_retention_hours=1)
        enforcer = CapacityPolicyEnforcer(config)

        # Record old metrics
        old_time = time.time() - (2 * 3600)  # 2 hours ago
        old_metrics = CapacityMetrics(
            current_load=5,
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=old_time,
            resource_utilization={}
        )

        enforcer.record_metrics(old_metrics)
        assert len(enforcer.metrics_history) == 1

        # Record current metrics
        current_metrics = CapacityMetrics(
            current_load=10,
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        enforcer.record_metrics(current_metrics)

        # Old metrics should be cleaned up
        assert len(enforcer.metrics_history) == 1
        latest = enforcer.get_current_metrics()
        assert latest is not None
        assert latest.current_load == current_metrics.current_load

    def test_capacity_limit_max_expansion(self) -> None:
        """Test that capacity doesn't exceed max expansion factor."""
        config = CapacityPolicyConfig(
            base_capacity=20,
            max_expansion_factor=1.5
        )
        enforcer = CapacityPolicyEnforcer(config)

        # Try to expand beyond max capacity
        metrics = CapacityMetrics(
            current_load=25,  # Requires expansion beyond 30
            max_capacity=20,
            warning_threshold=80,
            critical_threshold=95,
            timestamp=time.time(),
            resource_utilization={}
        )

        enforcer.record_metrics(metrics)
        result = enforcer.evaluate_capacity_request(10)

        assert not result["approved"]
        # Capacity should be expanded to max (30) but not beyond
        assert enforcer.current_capacity == int(config.base_capacity * config.max_expansion_factor)


class TestCapacityPolicyConfig:
    """Test CapacityPolicyConfig configuration."""

    def test_default_configuration(self) -> None:
        """Test default configuration values."""
        config = CapacityPolicyConfig()

        assert config.base_capacity == 20
        assert config.warning_threshold == 80
        assert config.critical_threshold == 95
        assert config.max_expansion_factor == 2.0
        assert config.expansion_step_size == 5
        assert config.cooldown_period_minutes == 30

    def test_custom_configuration(self) -> None:
        """Test custom configuration values."""
        config = CapacityPolicyConfig(
            base_capacity=30,
            warning_threshold=70,
            critical_threshold=90,
            max_expansion_factor=1.5,
            expansion_step_size=10
        )

        assert config.base_capacity == 30
        assert config.warning_threshold == 70
        assert config.critical_threshold == 90
        assert config.max_expansion_factor == 1.5
        assert config.expansion_step_size == 10


class TestCapacityPolicyFactory:
    """Test capacity policy factory function."""

    def test_create_default_policy(self) -> None:
        """Test creating policy with default configuration."""
        policy = create_capacity_policy()

        assert isinstance(policy, CapacityPolicyEnforcer)
        assert policy.config.base_capacity == 20

    def test_create_policy_with_config_file(self) -> None:
        """Test creating policy with config file (if exists)."""
        # This test would require a config file to exist
        # For now, we test the function doesn't error
        policy = create_capacity_policy(None)
        assert isinstance(policy, CapacityPolicyEnforcer)


class TestMonitoringIntegration:
    """Test monitoring integration features."""

    def test_start_monitoring(self) -> None:
        """Test starting capacity monitoring."""
        config = CapacityPolicyConfig()
        enforcer = CapacityPolicyEnforcer(config)

        enforcer.start_monitoring()

        assert enforcer._monitoring_active is True

    def test_stop_monitoring(self) -> None:
        """Test stopping capacity monitoring."""
        config = CapacityPolicyConfig()
        enforcer = CapacityPolicyEnforcer(config)

        enforcer.start_monitoring()
        enforcer.stop_monitoring()

        assert enforcer._monitoring_active is False