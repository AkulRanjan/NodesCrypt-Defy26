"""
CP5 Mitigation Engine
Turns RL decisions into real, enforceable mitigation actions.
All actions are: local, reversible, logged.
"""
import time
from datetime import datetime

class MitigationEngine:
    def __init__(self):
        self.mode = "NORMAL"
        self.min_fee = 0
        self.spam_delay_ms = 0
        self.history = []
        
    def apply(self, action):
        """Apply mitigation action based on RL decision."""
        timestamp = datetime.utcnow().isoformat()
        
        if action == 0:
            self._noop()
        elif action == 1:
            self._raise_min_fee()
        elif action == 2:
            self._deprioritize_spam()
        elif action == 3:
            self._defensive_mode()
        
        # Log action for audit
        self.history.append({
            "timestamp": timestamp,
            "action": action,
            "mode": self.mode,
            "min_fee": self.min_fee,
            "spam_delay_ms": self.spam_delay_ms
        })
        
    def _noop(self):
        """Monitor only - no active mitigation."""
        self.mode = "NORMAL"
        self.spam_delay_ms = 0
        print("[CP5] No action taken - monitoring mode")
        
    def _raise_min_fee(self):
        """Reject/deprioritize txs below fee threshold."""
        self.min_fee += 10
        self.mode = "FEE_FILTER"
        print(f"[CP5] Min fee raised to {self.min_fee} gwei")
        print(f"[CP5] Transactions below threshold will be deprioritized")
        
    def _deprioritize_spam(self):
        """Delay spam transaction broadcast."""
        self.mode = "SPAM_DEPRIORITIZATION"
        self.spam_delay_ms = 500
        print("[CP5] Spam transactions deprioritized")
        print(f"[CP5] Spam tx broadcast delayed by {self.spam_delay_ms}ms")
        
    def _defensive_mode(self):
        """Strict filtering + throttling."""
        self.mode = "DEFENSIVE"
        self.min_fee += 25
        self.spam_delay_ms = 1000
        print("[CP5] ⚠️ DEFENSIVE MODE ENABLED")
        print(f"[CP5] Min fee threshold: {self.min_fee} gwei")
        print(f"[CP5] Spam tx delay: {self.spam_delay_ms}ms")
        print("[CP5] Strict filtering active")
        
    def reset(self):
        """Reset to normal mode (reversible action)."""
        self.mode = "NORMAL"
        self.min_fee = 0
        self.spam_delay_ms = 0
        print("[CP5] System reset to NORMAL mode")
        
    def get_status(self):
        """Return current mitigation status."""
        return {
            "mode": self.mode,
            "min_fee": self.min_fee,
            "spam_delay_ms": self.spam_delay_ms,
            "history_count": len(self.history)
        }
    
    def should_admit_tx(self, tx_fee, spam_score):
        """Decide if a transaction should be admitted based on current policy."""
        if self.mode == "NORMAL":
            return True, 0
            
        if tx_fee < self.min_fee:
            return False, 0
            
        if spam_score > 0.5 and self.spam_delay_ms > 0:
            return True, self.spam_delay_ms
            
        return True, 0


# Singleton for global access
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = MitigationEngine()
    return _engine


if __name__ == "__main__":
    # Test the engine
    engine = MitigationEngine()
    print("=" * 60)
    print("[CP5] Mitigation Engine Test")
    print("=" * 60)
    
    for action in [0, 1, 2, 3]:
        print(f"\n--- Testing Action {action} ---")
        engine.apply(action)
        print(f"Status: {engine.get_status()}")
    
    print("\n--- Reset Test ---")
    engine.reset()
    print(f"Status: {engine.get_status()}")
