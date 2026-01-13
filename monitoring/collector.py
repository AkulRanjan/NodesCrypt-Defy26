"""
CP7 Metrics Collector
Collects system, ML, and RL metrics for monitoring and drift detection.
"""
import time
from collections import deque
from datetime import datetime

class MetricsCollector:
    def __init__(self, window_size=50):
        self.window_size = window_size
        self.history = {
            # System metrics
            "mempool_tx_count": deque(maxlen=window_size),
            "avg_fee_rate": deque(maxlen=window_size),
            "mitigation_mode": deque(maxlen=window_size),
            
            # ML metrics
            "spam_ratio": deque(maxlen=window_size),
            "spam_score": deque(maxlen=window_size),
            "false_positive": deque(maxlen=window_size),
            "model_confidence": deque(maxlen=window_size),
            
            # RL metrics
            "reward": deque(maxlen=window_size),
            "action": deque(maxlen=window_size),
            
            # Risk metrics
            "risk_score": deque(maxlen=window_size),
            "congestion_score": deque(maxlen=window_size),
        }
        self.timestamps = deque(maxlen=window_size)
        
    def update(self, **metrics):
        """Update metrics with new values."""
        self.timestamps.append(datetime.utcnow().isoformat())
        
        for key, value in metrics.items():
            if key in self.history:
                self.history[key].append(value)
                
    def get_avg(self, key):
        """Get average of a metric."""
        data = self.history.get(key, [])
        if not data:
            return 0
        return sum(data) / len(data)
    
    def get_latest(self, key):
        """Get latest value of a metric."""
        data = self.history.get(key, [])
        return data[-1] if data else None
    
    def summary(self):
        """Get summary of all metrics."""
        return {
            # System
            "avg_tx_count": self.get_avg("mempool_tx_count"),
            "avg_fee_rate": self.get_avg("avg_fee_rate"),
            
            # ML
            "avg_spam_ratio": self.get_avg("spam_ratio"),
            "avg_spam_score": self.get_avg("spam_score"),
            "fp_rate": self.get_avg("false_positive"),
            "avg_confidence": self.get_avg("model_confidence"),
            
            # RL
            "avg_reward": self.get_avg("reward"),
            "action_distribution": self._action_distribution(),
            
            # Risk
            "avg_risk_score": self.get_avg("risk_score"),
            "samples_collected": len(self.timestamps),
        }
    
    def _action_distribution(self):
        """Calculate action distribution."""
        actions = list(self.history["action"])
        if not actions:
            return {}
        total = len(actions)
        return {
            action: round(actions.count(action) / total, 2)
            for action in set(actions)
        }
    
    def get_trend(self, key, window=10):
        """Get trend direction for a metric."""
        data = list(self.history.get(key, []))
        if len(data) < window:
            return "STABLE"
        
        recent = data[-window:]
        older = data[-2*window:-window] if len(data) >= 2*window else data[:window]
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older) if older else recent_avg
        
        if recent_avg > older_avg * 1.2:
            return "INCREASING"
        elif recent_avg < older_avg * 0.8:
            return "DECREASING"
        return "STABLE"


# Singleton instance
_collector = None

def get_collector():
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


if __name__ == "__main__":
    print("=" * 60)
    print("[CP7] Metrics Collector Test")
    print("=" * 60)
    
    collector = MetricsCollector()
    
    # Simulate some metrics
    import random
    for i in range(20):
        collector.update(
            mempool_tx_count=random.randint(50, 150),
            spam_ratio=random.random() * 0.5,
            spam_score=random.random() * 0.4,
            false_positive=random.random() * 0.1,
            reward=-random.randint(1, 10),
            action=random.choice([0, 1, 2, 3]),
            risk_score=random.randint(50, 100),
            model_confidence=0.9 + random.random() * 0.1
        )
    
    print("\nMetrics Summary:")
    for k, v in collector.summary().items():
        print(f"  {k}: {v}")
    
    print(f"\nSpam Ratio Trend: {collector.get_trend('spam_ratio')}")
    print(f"Reward Trend: {collector.get_trend('reward')}")
