"""
Production monitoring and metrics service.
"""

import time
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict

logger = logging.getLogger("monitoring")


@dataclass
class Metric:
    """Metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    unit: str = "count"


class MetricsCollector:
    """
    Collect and aggregate application metrics.
    """

    def __init__(self, retention_minutes: int = 60):
        self.retention_minutes = retention_minutes
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)

    def record_counter(self, name: str, value: float = 1, tags: Dict = None):
        """Record a counter metric (cumulative)."""
        key = self._make_key(name, tags)
        self.counters[key] += value

        metric = Metric(
            name=name,
            value=self.counters[key],
            timestamp=datetime.utcnow(),
            tags=tags,
            unit="count"
        )
        self.metrics[name].append(metric)

    def record_gauge(self, name: str, value: float, tags: Dict = None):
        """Record a gauge metric (point-in-time value)."""
        key = self._make_key(name, tags)
        self.gauges[key] = value

        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags,
            unit="value"
        )
        self.metrics[name].append(metric)

    def record_timing(self, name: str, duration_ms: float, tags: Dict = None):
        """Record a timing metric."""
        key = self._make_key(name, tags)

        metric = Metric(
            name=name,
            value=duration_ms,
            timestamp=datetime.utcnow(),
            tags=tags,
            unit="ms"
        )
        self.metrics[name].append(metric)
        self.histograms[key].append(duration_ms)

    def _make_key(self, name: str, tags: Dict = None) -> str:
        """Create a unique key for metric with tags."""
        if not tags:
            return name

        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name},{tag_str}"

    def get_metrics(self, name: str = None, since: datetime = None) -> List[Dict]:
        """Get metrics, optionally filtered by name and time."""
        results = []

        if name:
            metrics_list = [name] if name in self.metrics else []
        else:
            metrics_list = list(self.metrics.keys())

        for metric_name in metrics_list:
            for metric in self.metrics[metric_name]:
                if since and metric.timestamp < since:
                    continue
                results.append(asdict(metric))

        return results

    def get_stats(self, name: str) -> Dict:
        """Get statistical summary for a metric."""
        if name not in self.metrics:
            return {}

        values = [m.value for m in self.metrics[name]]
        if not values:
            return {}

        return {
            "count": len(values),
            "sum": sum(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "last": values[-1] if values else None
        }

    def cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff = datetime.utcnow() - timedelta(minutes=self.retention_minutes)

        for name in list(self.metrics.keys()):
            # Remove old metrics
            while self.metrics[name] and self.metrics[name][0].timestamp < cutoff:
                self.metrics[name].popleft()

            # Remove empty queues
            if not self.metrics[name]:
                del self.metrics[name]


class PerformanceMonitor:
    """
    Monitor application performance metrics.
    """

    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.request_timings = {}

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass

    def start_request(self, request_id: str):
        """Start timing a request."""
        self.request_timings[request_id] = time.time()

    def end_request(
        self,
        request_id: str,
        endpoint: str,
        status_code: int,
        method: str = "GET"
    ):
        """End timing a request and record metrics."""
        if request_id not in self.request_timings:
            return

        start_time = self.request_timings.pop(request_id)
        duration_ms = (time.time() - start_time) * 1000

        # Record timing
        self.collector.record_timing(
            "http.request.duration",
            duration_ms,
            tags={
                "endpoint": endpoint,
                "method": method,
                "status": str(status_code)
            }
        )

        # Record counter
        self.collector.record_counter(
            "http.request.count",
            tags={
                "endpoint": endpoint,
                "method": method,
                "status": str(status_code)
            }
        )

        # Record status counter
        status_group = f"{status_code // 100}xx"
        self.collector.record_counter(
            f"http.status.{status_group}",
            tags={"endpoint": endpoint}
        )

    def record_error(self, error_type: str, endpoint: str = None):
        """Record an error occurrence."""
        self.collector.record_counter(
            "error.count",
            tags={
                "type": error_type,
                "endpoint": endpoint or "unknown"
            }
        )

    def record_cache_hit(self, cache_type: str = "redis"):
        """Record a cache hit."""
        self.collector.record_counter(
            "cache.hit",
            tags={"type": cache_type}
        )

    def record_cache_miss(self, cache_type: str = "redis"):
        """Record a cache miss."""
        self.collector.record_counter(
            "cache.miss",
            tags={"type": cache_type}
        )


class HealthChecker:
    """
    Health check service for monitoring system health.
    """

    def __init__(self):
        self.checks = {}
        self.last_check = {}
        self.status = "healthy"

    def register_check(self, name: str, check_func):
        """Register a health check function."""
        self.checks[name] = check_func

    async def run_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }

        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()

                self.last_check[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "timestamp": datetime.utcnow()
                }
                results["checks"][name] = self.last_check[name]

            except Exception as e:
                self.last_check[name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow()
                }
                results["checks"][name] = self.last_check[name]
                results["status"] = "degraded"

        # Overall status
        if any(c.get("status") == "error" for c in results["checks"].values()):
            results["status"] = "unhealthy"
        elif any(c.get("status") == "unhealthy" for c in results["checks"].values()):
            results["status"] = "degraded"

        self.status = results["status"]
        return results


class AlertManager:
    """
    Manage alerts based on metrics thresholds.
    """

    def __init__(self):
        self.alerts = []
        self.thresholds = {
            "error_rate": 0.01,  # 1% error rate
            "response_time_p95": 1000,  # 1 second
            "cache_hit_rate": 0.7,  # 70% hit rate
        }

    def check_thresholds(self, metrics: Dict):
        """Check metrics against thresholds and generate alerts."""
        new_alerts = []

        # Check error rate
        if "error_rate" in metrics and metrics["error_rate"] > self.thresholds["error_rate"]:
            new_alerts.append({
                "severity": "warning",
                "metric": "error_rate",
                "value": metrics["error_rate"],
                "threshold": self.thresholds["error_rate"],
                "message": f"High error rate: {metrics['error_rate']:.2%}",
                "timestamp": datetime.utcnow()
            })

        # Check response time
        if "response_time_p95" in metrics and metrics["response_time_p95"] > self.thresholds["response_time_p95"]:
            new_alerts.append({
                "severity": "warning",
                "metric": "response_time_p95",
                "value": metrics["response_time_p95"],
                "threshold": self.thresholds["response_time_p95"],
                "message": f"High response time: {metrics['response_time_p95']:.0f}ms",
                "timestamp": datetime.utcnow()
            })

        # Check cache hit rate
        if "cache_hit_rate" in metrics and metrics["cache_hit_rate"] < self.thresholds["cache_hit_rate"]:
            new_alerts.append({
                "severity": "info",
                "metric": "cache_hit_rate",
                "value": metrics["cache_hit_rate"],
                "threshold": self.thresholds["cache_hit_rate"],
                "message": f"Low cache hit rate: {metrics['cache_hit_rate']:.1%}",
                "timestamp": datetime.utcnow()
            })

        self.alerts.extend(new_alerts)
        return new_alerts

    def get_active_alerts(self, since_minutes: int = 5) -> List[Dict]:
        """Get active alerts from the last N minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=since_minutes)
        return [
            alert for alert in self.alerts
            if alert["timestamp"] > cutoff
        ]


# Global instances
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor(metrics_collector)
health_checker = HealthChecker()
alert_manager = AlertManager()


async def initialize_monitoring():
    """Initialize monitoring services."""

    # Register health checks
    async def check_database():
        """Check database connectivity."""
        try:
            # Check Supabase connection
            from app.core.database import supabase_client
            if supabase_client:
                # Simple query to check connection
                response = supabase_client.table("quotes").select("id").limit(1).execute()
                return True
        except:
            return False

    async def check_cache():
        """Check cache connectivity."""
        try:
            from app.services.cache import cache_service
            if cache_service and cache_service.redis_client:
                await cache_service.redis_client.ping()
                return True
        except:
            return False

    health_checker.register_check("database", check_database)
    health_checker.register_check("cache", check_cache)

    # Start cleanup task
    async def cleanup_task():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            metrics_collector.cleanup_old_metrics()

    asyncio.create_task(cleanup_task())

    logger.info("Monitoring services initialized")