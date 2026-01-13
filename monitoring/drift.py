"""
CP7 Drift Detection
Detects when environment changes and models need attention.

Drift conditions:
- HIGH_SPAM_ENV: spam ratio too high, environment hostile
- MODEL_TOO_AGGRESSIVE: high false positive rate
- RL_POLICY_DEGRADING: rewards declining
- CONGESTION_SPIKE: sudden congestion increase
"""

class DriftDetector:
    def __init__(self):
        self.thresholds = {
            "spam_ratio_high": 0.6,
            "fp_rate_high": 0.25,
            "reward_low": -50,
            "risk_score_critical": 90,
            "confidence_low": 0.7,
        }
        self.alert_history = []
        
    def detect(self, metrics):
        """
        Detect drift based on metrics summary.
        Returns list of alerts.
        """
        alerts = []
        
        # Check spam environment
        if metrics.get("avg_spam_ratio", 0) > self.thresholds["spam_ratio_high"]:
            alerts.append({
                "type": "HIGH_SPAM_ENV",
                "severity": "HIGH",
                "message": f"Spam ratio {metrics['avg_spam_ratio']:.2f} exceeds threshold",
                "action": "Force defensive mode"
            })
        
        # Check model aggressiveness
        if metrics.get("fp_rate", 0) > self.thresholds["fp_rate_high"]:
            alerts.append({
                "type": "MODEL_TOO_AGGRESSIVE",
                "severity": "MEDIUM",
                "message": f"False positive rate {metrics['fp_rate']:.2f} too high",
                "action": "Lower spam threshold"
            })
        
        # Check RL policy health
        if metrics.get("avg_reward", 0) < self.thresholds["reward_low"]:
            alerts.append({
                "type": "RL_POLICY_DEGRADING",
                "severity": "HIGH",
                "message": f"Average reward {metrics['avg_reward']:.2f} below threshold",
                "action": "Freeze RL, use safe policy"
            })
        
        # Check risk level
        if metrics.get("avg_risk_score", 0) > self.thresholds["risk_score_critical"]:
            alerts.append({
                "type": "CRITICAL_RISK",
                "severity": "CRITICAL",
                "message": f"Risk score {metrics['avg_risk_score']:.0f} is critical",
                "action": "Maximum defensive posture"
            })
        
        # Check model confidence
        if metrics.get("avg_confidence", 1) < self.thresholds["confidence_low"]:
            alerts.append({
                "type": "LOW_MODEL_CONFIDENCE",
                "severity": "MEDIUM",
                "message": f"Model confidence {metrics['avg_confidence']:.2f} too low",
                "action": "Consider model retraining"
            })
        
        # Store alerts
        self.alert_history.extend(alerts)
        
        return alerts
    
    def get_recent_alerts(self, n=10):
        """Get most recent alerts."""
        return self.alert_history[-n:]


def detect_drift(metrics):
    """Convenience function for drift detection."""
    detector = DriftDetector()
    return detector.detect(metrics)


if __name__ == "__main__":
    print("=" * 60)
    print("[CP7] Drift Detection Test")
    print("=" * 60)
    
    # Test with different metric scenarios
    scenarios = [
        {"name": "Normal", "avg_spam_ratio": 0.2, "fp_rate": 0.1, "avg_reward": -10, "avg_risk_score": 50, "avg_confidence": 0.95},
        {"name": "High Spam", "avg_spam_ratio": 0.8, "fp_rate": 0.1, "avg_reward": -20, "avg_risk_score": 70, "avg_confidence": 0.85},
        {"name": "Aggressive Model", "avg_spam_ratio": 0.3, "fp_rate": 0.4, "avg_reward": -15, "avg_risk_score": 60, "avg_confidence": 0.90},
        {"name": "Policy Decay", "avg_spam_ratio": 0.4, "fp_rate": 0.2, "avg_reward": -80, "avg_risk_score": 75, "avg_confidence": 0.80},
    ]
    
    detector = DriftDetector()
    
    for scenario in scenarios:
        name = scenario.pop("name")
        alerts = detector.detect(scenario)
        print(f"\n{name} scenario:")
        if alerts:
            for alert in alerts:
                print(f"  🚨 [{alert['severity']}] {alert['type']}: {alert['message']}")
        else:
            print("  ✓ No drift detected")
