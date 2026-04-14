"""Capacity policy implementation.

English:
Implements the 20/8 capacity strategy with controlled upward expansion mode.
Monitors system capacity and enforces policy constraints.

Chinese:
实现20/8容量策略与受控向上扩展模式。
监控系统容量并强制执行策略约束。
"""

from __future__ import annotations

import dataclasses
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class CapacityState(Enum):
    """Capacity state enumeration."""

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    OVERLOADED = "overloaded"


@dataclass(slots=True)
class CapacityMetrics:
    """System capacity metrics."""

    current_load: int
    max_capacity: int
    warning_threshold: int
    critical_threshold: int
    timestamp: float
    resource_utilization: Dict[str, float]

    @property
    def utilization_rate(self) -> float:
        """Calculate current utilization rate."""
        return self.current_load / self.max_capacity if self.max_capacity > 0 else 0.0

    @property
    def state(self) -> CapacityState:
        """Get current capacity state."""
        if self.utilization_rate >= 1.0:
            return CapacityState.OVERLOADED
        elif self.utilization_rate >= self.critical_threshold / 100:
            return CapacityState.CRITICAL
        elif self.utilization_rate >= self.warning_threshold / 100:
            return CapacityState.WARNING
        else:
            return CapacityState.NORMAL

    def can_accept_load(self, required_capacity: int) -> bool:
        """Check if system can accept additional load."""
        return (self.current_load + required_capacity) <= self.max_capacity


@dataclass(slots=True)
class CapacityPolicyConfig:
    """Configuration for capacity policy."""

    # Base capacity settings
    base_capacity: int = 20  # Stable capacity (20 units)
    warning_threshold: int = 80  # 80% utilization warning
    critical_threshold: int = 95  # 95% utilization critical

    # Expansion settings
    max_expansion_factor: float = 2.0  # Maximum 2x expansion
    expansion_step_size: int = 5  # Increase by 5 units at a time
    cooldown_period_minutes: int = 30  # Minimum time between expansions

    # Monitoring settings
    metrics_retention_hours: int = 24  # Keep metrics for 24 hours
    check_interval_seconds: int = 60  # Check every 60 seconds

    # Resource-specific thresholds
    cpu_threshold_percent: float = 80.0
    memory_threshold_percent: float = 85.0
    disk_threshold_percent: float = 90.0


class CapacityPolicyEnforcer:
    """Enforces capacity policy with controlled expansion."""

    def __init__(self, config: CapacityPolicyConfig):
        self.config = config
        self.metrics_history: List[CapacityMetrics] = []
        self.last_expansion_time: Optional[float] = None
        self.current_capacity = config.base_capacity
        self._monitoring_active = False

    def record_metrics(self, metrics: CapacityMetrics) -> None:
        """Record capacity metrics."""
        self.metrics_history.append(metrics)

        # Clean up old metrics
        cutoff_time = time.time() - (self.config.metrics_retention_hours * 3600)
        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]

    def get_current_metrics(self) -> Optional[CapacityMetrics]:
        """Get the most recent metrics."""
        return self.metrics_history[-1] if self.metrics_history else None

    def evaluate_capacity_request(
        self, requested_capacity: int, resource_check: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Evaluate a capacity request."""
        current_metrics = self.get_current_metrics()

        if not current_metrics:
            return {
                "approved": True,
                "reason": "No metrics available, approving request",
                "new_capacity": self.current_capacity,
            }

        # Check if we have enough capacity
        if not current_metrics.can_accept_load(requested_capacity):
            # Check if we can expand
            can_expand = self._can_expand_capacity(current_metrics)

            if can_expand:
                previous_capacity = self.current_capacity
                new_capacity = self._expand_capacity(requested_capacity, current_metrics)
                return {
                    "approved": True,
                    "reason": "Capacity expanded to accommodate request",
                    "new_capacity": new_capacity,
                    "previous_capacity": previous_capacity,
                }
            else:
                return {
                    "approved": False,
                    "reason": "System at capacity and cannot expand",
                    "current_capacity": self.current_capacity,
                    "current_load": current_metrics.current_load,
                    "utilization_rate": current_metrics.utilization_rate,
                }

        # Check resource constraints
        if resource_check:
            violation = self._check_resource_constraints(resource_check)
            if violation:
                return {
                    "approved": False,
                    "reason": f"Resource constraint violation: {violation}",
                    "resource_check": resource_check,
                }

        return {
            "approved": True,
            "reason": "Capacity available",
            "remaining_capacity": self.current_capacity
            - current_metrics.current_load
            - requested_capacity,
        }

    def _can_expand_capacity(self, current_metrics: CapacityMetrics) -> bool:
        """Check if capacity can be expanded."""
        # Check if we're already at max expansion
        if self.current_capacity >= self.config.base_capacity * self.config.max_expansion_factor:
            return False

        # Check cooldown period
        if (
            self.last_expansion_time
            and time.time() - self.last_expansion_time < self.config.cooldown_period_minutes * 60
        ):
            return False

        # Only expand in WARNING or CRITICAL state
        return current_metrics.state in [CapacityState.WARNING, CapacityState.CRITICAL]

    def _expand_capacity(self, requested_capacity: int, current_metrics: CapacityMetrics) -> int:
        """Expand capacity to accommodate request."""
        # Calculate required expansion
        required_total = current_metrics.current_load + requested_capacity
        expansion_needed = required_total - self.current_capacity

        # Determine expansion size (round up to step size)
        expansion_steps = max(
            1,
            int(
                (expansion_needed + self.config.expansion_step_size - 1)
                / self.config.expansion_step_size
            ),
        )

        # Calculate new capacity with limits
        proposed_new_capacity = min(
            self.current_capacity + (expansion_steps * self.config.expansion_step_size),
            int(self.config.base_capacity * self.config.max_expansion_factor),
        )

        self.current_capacity = proposed_new_capacity
        self.last_expansion_time = time.time()

        return self.current_capacity

    def _check_resource_constraints(self, resource_check: Dict[str, float]) -> Optional[str]:
        """Check if resource constraints are violated."""
        if resource_check.get("cpu", 0) > self.config.cpu_threshold_percent:
            return f"CPU usage {resource_check['cpu']:.1f}% exceeds threshold {self.config.cpu_threshold_percent}%"

        if resource_check.get("memory", 0) > self.config.memory_threshold_percent:
            return f"Memory usage {resource_check['memory']:.1f}% exceeds threshold {self.config.memory_threshold_percent}%"

        if resource_check.get("disk", 0) > self.config.disk_threshold_percent:
            return f"Disk usage {resource_check['disk']:.1f}% exceeds threshold {self.config.disk_threshold_percent}%"

        return None

    def get_capacity_report(self) -> Dict[str, Any]:
        """Generate capacity report for monitoring."""
        current_metrics = self.get_current_metrics()

        report = {
            "timestamp": time.time(),
            "policy_config": dataclasses.asdict(self.config),
            "current_capacity": self.current_capacity,
            "base_capacity": self.config.base_capacity,
            "expansion_factor": self.current_capacity / self.config.base_capacity,
            "max_expansion_factor": self.config.max_expansion_factor,
            "last_expansion_time": self.last_expansion_time,
            "monitoring_active": self._monitoring_active,
        }

        if current_metrics:
            report.update(
                {
                    "current_metrics": dataclasses.asdict(current_metrics),
                    "state": current_metrics.state.value,
                    "utilization_rate": current_metrics.utilization_rate,
                }
            )

            # Add trend analysis
            if len(self.metrics_history) >= 3:
                recent_metrics = self.metrics_history[-3:]
                trend = self._analyze_trend(recent_metrics)
                report["trend"] = trend

        return report

    def _analyze_trend(self, metrics: List[CapacityMetrics]) -> Dict[str, Any]:
        """Analyze capacity trend."""
        if len(metrics) < 2:
            return {"trend": "stable", "confidence": 0.0}

        utilization_rates = [m.utilization_rate for m in metrics]

        # Calculate trend
        if utilization_rates[-1] > utilization_rates[0] + 0.1:
            trend = "increasing"
        elif utilization_rates[-1] < utilization_rates[0] - 0.1:
            trend = "decreasing"
        else:
            trend = "stable"

        # Calculate volatility
        volatility = max(
            abs(utilization_rates[i] - utilization_rates[i - 1])
            for i in range(1, len(utilization_rates))
        )

        return {
            "trend": trend,
            "volatility": volatility,
            "confidence": min(1.0, len(metrics) / 10.0),
        }

    def start_monitoring(self) -> None:
        """Start capacity monitoring."""
        self._monitoring_active = True

    def stop_monitoring(self) -> None:
        """Stop capacity monitoring."""
        self._monitoring_active = False


# Factory function to create policy enforcer with config
def create_capacity_policy(config_path: Optional[Path] = None) -> CapacityPolicyEnforcer:
    """Create capacity policy enforcer with optional config file."""
    if config_path and config_path.exists():
        # Load config from file (could be JSON/YAML)
        # For now, use default config
        pass

    config = CapacityPolicyConfig()
    return CapacityPolicyEnforcer(config)
