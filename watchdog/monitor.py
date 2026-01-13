"""
Watchdog & Resilience Service
Provides health monitoring, failover, and safe fallback modes.

Features:
- Service health checks
- Automatic failover
- Safe fallback policies
- Alert generation
"""
import time
import threading
from typing import Dict, List, Callable, Optional
from datetime import datetime
from enum import Enum

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """Result of a health check."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.status = ServiceStatus.UNKNOWN
        self.last_check = None
        self.response_time_ms = 0
        self.error_message = None
        self.consecutive_failures = 0
        self.metadata = {}
        
    def to_dict(self) -> dict:
        return {
            "service": self.service_name,
            "status": self.status.value,
            "last_check": self.last_check,
            "response_time_ms": self.response_time_ms,
            "error": self.error_message,
            "consecutive_failures": self.consecutive_failures,
            "metadata": self.metadata
        }


class FallbackPolicy(Enum):
    """Failover behavior when services fail."""
    FAIL_OPEN = "fail_open"      # Continue with defaults (production-safe)
    FAIL_CLOSED = "fail_closed"  # Block everything (strict security)
    MONITORING_ONLY = "monitoring_only"  # Log but don't act


class Watchdog:
    """
    Service watchdog for health monitoring and failover.
    """
    
    def __init__(self):
        self.services: Dict[str, HealthCheck] = {}
        self.check_functions: Dict[str, Callable] = {}
        self.fallback_policy = FallbackPolicy.FAIL_OPEN
        self.alert_callbacks: List[Callable] = []
        self.check_interval_seconds = 30
        self.failure_threshold = 3
        self.is_running = False
        self._thread = None
        
        # Fallback settings
        self.fallback_settings = {
            "mitigation_mode": "NORMAL",
            "min_fee": 0,
            "rl_enabled": False,
            "ml_enabled": False,
            "rules_enabled": True
        }
        
        # Current system state
        self.system_healthy = True
        self.degraded_services: List[str] = []
        
    def register_service(self, name: str, check_func: Callable[[], bool], metadata: dict = None):
        """Register a service for health monitoring."""
        self.services[name] = HealthCheck(name)
        self.check_functions[name] = check_func
        if metadata:
            self.services[name].metadata = metadata
    
    def check_service(self, name: str) -> HealthCheck:
        """Check health of a single service."""
        if name not in self.services:
            raise ValueError(f"Unknown service: {name}")
        
        health = self.services[name]
        check_func = self.check_functions[name]
        
        start_time = time.time()
        try:
            result = check_func()
            health.response_time_ms = int((time.time() - start_time) * 1000)
            
            if result:
                health.status = ServiceStatus.HEALTHY
                health.consecutive_failures = 0
                health.error_message = None
            else:
                health.status = ServiceStatus.DEGRADED
                health.consecutive_failures += 1
                
        except Exception as e:
            health.response_time_ms = int((time.time() - start_time) * 1000)
            health.status = ServiceStatus.UNHEALTHY
            health.consecutive_failures += 1
            health.error_message = str(e)
        
        health.last_check = datetime.utcnow().isoformat()
        
        # Check if we need to trigger alert
        if health.consecutive_failures >= self.failure_threshold:
            self._trigger_alert(name, health)
        
        return health
    
    def check_all(self) -> Dict[str, HealthCheck]:
        """Check health of all registered services."""
        for name in self.services:
            self.check_service(name)
        
        # Update system health
        self._update_system_health()
        
        return self.services
    
    def _update_system_health(self):
        """Update overall system health status."""
        self.degraded_services = []
        
        for name, health in self.services.items():
            if health.status in [ServiceStatus.DEGRADED, ServiceStatus.UNHEALTHY]:
                self.degraded_services.append(name)
        
        self.system_healthy = len(self.degraded_services) == 0
    
    def _trigger_alert(self, service_name: str, health: HealthCheck):
        """Trigger alert for service failure."""
        alert = {
            "type": "SERVICE_FAILURE",
            "service": service_name,
            "status": health.status.value,
            "consecutive_failures": health.consecutive_failures,
            "error": health.error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except:
                pass
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def get_fallback_settings(self) -> dict:
        """Get current fallback settings based on system health."""
        if self.system_healthy:
            return {
                "mitigation_mode": None,  # Use normal decision
                "rl_enabled": True,
                "ml_enabled": True,
                "rules_enabled": True,
                "fallback_active": False
            }
        
        # System is degraded - apply fallback
        settings = self.fallback_settings.copy()
        settings["fallback_active"] = True
        settings["degraded_services"] = self.degraded_services
        
        if self.fallback_policy == FallbackPolicy.FAIL_CLOSED:
            settings["mitigation_mode"] = "DEFENSIVE"
            settings["min_fee"] = 50
        elif self.fallback_policy == FallbackPolicy.MONITORING_ONLY:
            settings["mitigation_mode"] = "NORMAL"
            settings["rl_enabled"] = False
            settings["ml_enabled"] = False
        
        return settings
    
    def is_service_healthy(self, name: str) -> bool:
        """Check if a specific service is healthy."""
        if name not in self.services:
            return False
        return self.services[name].status == ServiceStatus.HEALTHY
    
    def get_status(self) -> dict:
        """Get overall system status."""
        return {
            "system_healthy": self.system_healthy,
            "fallback_policy": self.fallback_policy.value,
            "fallback_active": not self.system_healthy,
            "degraded_services": self.degraded_services,
            "services": {name: h.to_dict() for name, h in self.services.items()}
        }
    
    def start_background_checks(self):
        """Start background health check thread."""
        if self.is_running:
            return
        
        self.is_running = True
        self._thread = threading.Thread(target=self._background_check_loop, daemon=True)
        self._thread.start()
    
    def stop_background_checks(self):
        """Stop background health checks."""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _background_check_loop(self):
        """Background loop for periodic health checks."""
        while self.is_running:
            self.check_all()
            time.sleep(self.check_interval_seconds)


# Default health check functions
def check_postgres():
    """Check PostgreSQL connectivity."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="checkpoint",
            user="cp",
            password="cp",
            connect_timeout=5
        )
        conn.close()
        return True
    except:
        return False

def check_ml_service():
    """Check ML service health."""
    try:
        import requests
        response = requests.get("http://127.0.0.1:8002/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_feature_extractor():
    """Check feature extractor (via recent data in DB)."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="checkpoint",
            user="cp",
            password="cp"
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM mempool_features 
            WHERE snapshot_time > NOW() - INTERVAL '1 minute'
        """)
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except:
        return False


# Singleton instance
_watchdog = None

def get_watchdog() -> Watchdog:
    global _watchdog
    if _watchdog is None:
        _watchdog = Watchdog()
        # Register default services
        _watchdog.register_service("postgres", check_postgres, {"type": "database"})
        _watchdog.register_service("ml_service", check_ml_service, {"type": "api"})
        _watchdog.register_service("feature_extractor", check_feature_extractor, {"type": "worker"})
    return _watchdog


if __name__ == "__main__":
    print("=" * 60)
    print("[WATCHDOG] Service Health Test")
    print("=" * 60)
    
    watchdog = get_watchdog()
    
    # Check all services
    results = watchdog.check_all()
    
    print("\nService Status:")
    for name, health in results.items():
        status_icon = "✓" if health.status == ServiceStatus.HEALTHY else "✗"
        print(f"  {status_icon} {name}: {health.status.value} ({health.response_time_ms}ms)")
        if health.error_message:
            print(f"      Error: {health.error_message}")
    
    print(f"\nSystem Healthy: {watchdog.system_healthy}")
    print(f"Fallback Policy: {watchdog.fallback_policy.value}")
    
    if watchdog.degraded_services:
        print(f"Degraded Services: {watchdog.degraded_services}")
    
    print("\nFallback Settings:")
    for key, value in watchdog.get_fallback_settings().items():
        print(f"  {key}: {value}")
