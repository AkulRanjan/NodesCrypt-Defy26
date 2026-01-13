"""
CP7 Self-Healing Actions
Safe, controlled responses to detected drift.

IMPORTANT: We do NOT auto-retrain during demo.
We trigger safe, reversible responses only.
"""

class SelfHealer:
    def __init__(self, mitigation_engine=None):
        self.mitigation_engine = mitigation_engine
        self.rl_frozen = False
        self.healing_history = []
        
    def heal(self, alerts):
        """
        Apply safe healing actions based on alerts.
        Returns list of actions taken.
        """
        actions_taken = []
        
        for alert in alerts:
            alert_type = alert["type"]
            
            if alert_type == "HIGH_SPAM_ENV":
                action = self._handle_high_spam()
                actions_taken.append(action)
                
            elif alert_type == "MODEL_TOO_AGGRESSIVE":
                action = self._handle_aggressive_model()
                actions_taken.append(action)
                
            elif alert_type == "RL_POLICY_DEGRADING":
                action = self._handle_policy_degrading()
                actions_taken.append(action)
                
            elif alert_type == "CRITICAL_RISK":
                action = self._handle_critical_risk()
                actions_taken.append(action)
                
            elif alert_type == "LOW_MODEL_CONFIDENCE":
                action = self._handle_low_confidence()
                actions_taken.append(action)
        
        self.healing_history.extend(actions_taken)
        return actions_taken
    
    def _handle_high_spam(self):
        """Force defensive mode."""
        if self.mitigation_engine:
            self.mitigation_engine._defensive_mode()
        print("[CP7] 🔧 HEAL: Forcing DEFENSIVE mode due to high spam")
        return {"action": "FORCE_DEFENSIVE", "reason": "HIGH_SPAM_ENV"}
    
    def _handle_aggressive_model(self):
        """Lower spam threshold to reduce false positives."""
        if self.mitigation_engine:
            self.mitigation_engine.min_fee = max(0, self.mitigation_engine.min_fee - 10)
            print(f"[CP7] 🔧 HEAL: Lowered min fee to {self.mitigation_engine.min_fee}")
        else:
            print("[CP7] 🔧 HEAL: Would lower spam threshold")
        return {"action": "LOWER_THRESHOLD", "reason": "MODEL_TOO_AGGRESSIVE"}
    
    def _handle_policy_degrading(self):
        """Freeze RL and use safe fallback."""
        self.rl_frozen = True
        print("[CP7] 🔧 HEAL: RL policy FROZEN - using safe fallback")
        return {"action": "FREEZE_RL", "reason": "RL_POLICY_DEGRADING"}
    
    def _handle_critical_risk(self):
        """Maximum defensive posture."""
        if self.mitigation_engine:
            self.mitigation_engine._defensive_mode()
            self.mitigation_engine.min_fee += 50
            print(f"[CP7] 🔧 HEAL: CRITICAL - max defense, fee={self.mitigation_engine.min_fee}")
        else:
            print("[CP7] 🔧 HEAL: Would enable maximum defensive posture")
        return {"action": "MAX_DEFENSE", "reason": "CRITICAL_RISK"}
    
    def _handle_low_confidence(self):
        """Flag for model review (no auto-retrain)."""
        print("[CP7] 🔧 HEAL: Model flagged for manual review")
        return {"action": "FLAG_FOR_REVIEW", "reason": "LOW_MODEL_CONFIDENCE"}
    
    def is_rl_frozen(self):
        """Check if RL is frozen."""
        return self.rl_frozen
    
    def unfreeze_rl(self):
        """Manually unfreeze RL."""
        self.rl_frozen = False
        print("[CP7] RL policy unfrozen")
    
    def get_healing_history(self):
        """Get history of healing actions."""
        return self.healing_history


def heal(alerts, mitigation_engine=None):
    """Convenience function for healing."""
    healer = SelfHealer(mitigation_engine)
    return healer.heal(alerts)


if __name__ == "__main__":
    print("=" * 60)
    print("[CP7] Self-Healing Test")
    print("=" * 60)
    
    # Test with sample alerts
    test_alerts = [
        {"type": "HIGH_SPAM_ENV", "severity": "HIGH", "message": "Test"},
        {"type": "MODEL_TOO_AGGRESSIVE", "severity": "MEDIUM", "message": "Test"},
        {"type": "RL_POLICY_DEGRADING", "severity": "HIGH", "message": "Test"},
    ]
    
    healer = SelfHealer()
    actions = healer.heal(test_alerts)
    
    print("\nActions taken:")
    for action in actions:
        print(f"  • {action['action']} (reason: {action['reason']})")
    
    print(f"\nRL Frozen: {healer.is_rl_frozen()}")
