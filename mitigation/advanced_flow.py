"""
Advanced Decision Flow
Integrates all advanced features: threat intel, simulation, rules, ML, RL, explainability.

This is the complete decision pipeline that ties everything together.
"""
import sys
import os
import time
from typing import Dict, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from threat_intel.lookup import get_intel, get_address_features
from simulator.runner import get_simulator, simulate_tx
from rules.engine import get_engine as get_rules_engine, evaluate_rules
from ml.explainer import get_explainer, explain_prediction
from watchdog.monitor import get_watchdog
from audit.logger import get_logger as get_audit_logger
from mitigation.engine import get_engine as get_mitigation_engine

# Import RL
try:
    from rl.policy import decide_action_with_name
    RL_AVAILABLE = True
except:
    RL_AVAILABLE = False


class DecisionContext:
    """Context containing all information for a decision."""
    
    def __init__(self, tx_data: dict):
        self.tx_data = tx_data
        self.features = {}
        self.reputation = {}
        self.simulation = None
        self.rule_result = None
        self.ml_scores = {}
        self.rl_state = []
        self.rl_action = None
        self.explanation = None
        self.final_action = None
        self.decision_source = None
        
    def to_dict(self) -> dict:
        return {
            "tx_hash": self.tx_data.get("hash", "unknown"),
            "features": self.features,
            "reputation": self.reputation,
            "simulation_risk": self.simulation.get_risk_score() if self.simulation else None,
            "rule_matched": self.rule_result["rule_id"] if self.rule_result else None,
            "ml_scores": self.ml_scores,
            "rl_action": self.rl_action,
            "final_action": self.final_action,
            "decision_source": self.decision_source
        }


class AdvancedDecisionEngine:
    """
    Advanced decision engine integrating all features.
    
    Pipeline:
    1. Threat Intel lookup (reputation)
    2. Rules evaluation (fast path)
    3. ML scoring (spam, congestion)
    4. Simulation (high-risk only)
    5. RL decision (if enabled)
    6. Explainability
    7. Audit logging
    """
    
    def __init__(self):
        self.intel = get_intel()
        self.simulator = get_simulator()
        self.rules_engine = get_rules_engine()
        self.explainer = get_explainer()
        self.watchdog = get_watchdog()
        self.audit_logger = get_audit_logger()
        self.mitigation_engine = get_mitigation_engine()
        
        # Thresholds
        self.simulation_value_threshold = 1_000_000_000_000_000_000  # 1 ETH
        self.high_risk_spam_threshold = 0.7
        
        # Stats
        self.decisions_made = 0
        self.rules_fired = 0
        self.simulations_run = 0
        
    def decide(self, tx_data: dict, features: dict = None, ml_scores: dict = None) -> DecisionContext:
        """
        Make a decision for a transaction.
        
        Args:
            tx_data: Raw transaction data
            features: Pre-computed features (optional)
            ml_scores: Pre-computed ML scores (optional)
            
        Returns:
            DecisionContext with full decision information
        """
        ctx = DecisionContext(tx_data)
        ctx.features = features or {}
        ctx.ml_scores = ml_scores or {}
        
        # Check system health first
        fallback = self.watchdog.get_fallback_settings()
        if fallback.get("fallback_active"):
            return self._apply_fallback(ctx, fallback)
        
        # Step 1: Threat Intel
        sender = tx_data.get("from", tx_data.get("sender", ""))
        if sender:
            ctx.reputation = self.intel.lookup(sender)
            intel_features = self.intel.get_features(sender)
            ctx.features.update(intel_features)
        
        # Step 2: Rules evaluation (fast path)
        rule_context = {
            **ctx.features,
            **ctx.ml_scores,
            "value": int(tx_data.get("value", 0)),
            "is_blacklisted": ctx.reputation.get("is_blacklisted", False),
            "is_whitelisted": ctx.reputation.get("is_whitelisted", False),
            "reputation_score": ctx.reputation.get("reputation_score", 0.5),
        }
        
        ctx.rule_result = self.rules_engine.evaluate(rule_context)
        
        if ctx.rule_result:
            self.rules_fired += 1
            
            # If rule says ALLOW or BLOCK, use it directly
            if ctx.rule_result["action"] in ["ALLOW", "BLOCK"]:
                ctx.final_action = self._action_to_int(ctx.rule_result["action"])
                ctx.decision_source = "rule"
                ctx.explanation = self.explainer.explain_rule_match(ctx.rule_result, rule_context)
                self._finalize_decision(ctx)
                return ctx
        
        # Step 3: ML scoring (if not provided)
        if "spam_score" not in ctx.ml_scores:
            ctx.ml_scores["spam_score"] = ctx.features.get("spam_score", 0.5)
        
        # Step 4: Simulation (for high-risk transactions)
        spam_score = ctx.ml_scores.get("spam_score", 0)
        value = int(tx_data.get("value", 0))
        
        if self.simulator.should_simulate(tx_data, spam_score):
            ctx.simulation = self.simulator.simulate(tx_data)
            ctx.features["simulation_risk"] = ctx.simulation.get_risk_score()
            self.simulations_run += 1
        
        # Step 5: RL decision
        if RL_AVAILABLE and fallback.get("rl_enabled", True):
            ctx.rl_state = self._build_state_vector(ctx)
            action, action_name = decide_action_with_name(ctx.rl_state)
            ctx.rl_action = action
            ctx.final_action = action
            ctx.decision_source = "rl"
        else:
            # Use rule result or default
            if ctx.rule_result:
                ctx.final_action = self._action_to_int(ctx.rule_result["action"])
                ctx.decision_source = "rule"
            else:
                ctx.final_action = 0  # DO_NOTHING
                ctx.decision_source = "default"
        
        # Step 6: Explainability
        if ctx.decision_source == "rl" or ctx.decision_source == "ml":
            ctx.explanation = self.explainer.explain(
                ctx.features,
                ctx.ml_scores.get("spam_score", 0.5)
            )
        elif ctx.rule_result:
            ctx.explanation = self.explainer.explain_rule_match(ctx.rule_result, rule_context)
        
        # Finalize
        self._finalize_decision(ctx)
        return ctx
    
    def _build_state_vector(self, ctx: DecisionContext) -> list:
        """Build RL state vector from context."""
        return [
            ctx.features.get("tx_count", 5),
            ctx.features.get("avg_fee_rate", 0.001),
            ctx.ml_scores.get("congestion_score", 1000),
            ctx.ml_scores.get("spam_score", 0.25),
            ctx.features.get("spam_ratio", 0.1)
        ]
    
    def _action_to_int(self, action_str: str) -> int:
        """Convert action string to integer."""
        action_map = {
            "ALLOW": 0,
            "DO_NOTHING": 0,
            "FLAG": 1,
            "RAISE_FEE_THRESHOLD": 1,
            "DEPRIORITIZE": 2,
            "DEPRIORITIZE_SPAM": 2,
            "BLOCK": 3,
            "DEFENSIVE": 3,
            "DEFENSIVE_MODE": 3
        }
        return action_map.get(action_str.upper(), 0)
    
    def _apply_fallback(self, ctx: DecisionContext, fallback: dict) -> DecisionContext:
        """Apply fallback decision when system is degraded."""
        ctx.decision_source = "fallback"
        
        if fallback.get("mitigation_mode") == "DEFENSIVE":
            ctx.final_action = 3
        else:
            ctx.final_action = 0
        
        return ctx
    
    def _finalize_decision(self, ctx: DecisionContext):
        """Finalize and log the decision."""
        self.decisions_made += 1
        
        # Apply mitigation
        self.mitigation_engine.apply(ctx.final_action)
        
        # Log to audit
        incident_id, payload = self.audit_logger.generate_incident(
            state=ctx.rl_state or [0, 0, 0, 0, 0],
            action=ctx.final_action,
            mode=self.mitigation_engine.mode,
            confidence=ctx.explanation.confidence if ctx.explanation else 0.5
        )
        
        # Add explanation hash to payload
        if ctx.explanation:
            payload["explanation_hash"] = ctx.explanation.explanation_hash
    
    def get_stats(self) -> dict:
        """Get engine statistics."""
        return {
            "decisions_made": self.decisions_made,
            "rules_fired": self.rules_fired,
            "simulations_run": self.simulations_run,
            "simulator_stats": self.simulator.get_stats(),
            "mitigation_status": self.mitigation_engine.get_status()
        }


# Singleton instance
_decision_engine = None

def get_decision_engine() -> AdvancedDecisionEngine:
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = AdvancedDecisionEngine()
    return _decision_engine


if __name__ == "__main__":
    print("=" * 60)
    print("[ADVANCED] Decision Engine Test")
    print("=" * 60)
    
    engine = AdvancedDecisionEngine()
    
    # Test transactions
    test_txs = [
        {
            "hash": "0xnormal123",
            "from": "0xuser1234567890abcdef1234567890abcdef1234",
            "to": "0xcontract",
            "value": 100000000000000000,  # 0.1 ETH
            "data": "",
            "gas": 21000
        },
        {
            "hash": "0xblacklist456",
            "from": "0xbad0000000000000000000000000000000000001",
            "to": "0xvictim",
            "value": 1000000000000000000,  # 1 ETH
            "data": "",
            "gas": 50000
        },
        {
            "hash": "0xhighvalue789",
            "from": "0xwhale0000000000000000000000000000000001",
            "to": "0xexchange",
            "value": 50000000000000000000000,  # 50000 ETH
            "data": "0x095ea7b3",  # Approve
            "gas": 100000
        }
    ]
    
    for tx in test_txs:
        print(f"\n--- TX: {tx['hash'][:16]}... ---")
        
        ctx = engine.decide(tx, ml_scores={"spam_score": 0.3})
        
        print(f"  Sender: {tx['from'][:20]}...")
        print(f"  Reputation: {ctx.reputation.get('risk_level', 'N/A')}")
        print(f"  Rule Matched: {ctx.rule_result['rule_id'] if ctx.rule_result else 'None'}")
        print(f"  Final Action: {ctx.final_action}")
        print(f"  Decision Source: {ctx.decision_source}")
        if ctx.explanation:
            print(f"  Explanation: {ctx.explanation.get_summary()[:60]}...")
    
    print(f"\n--- Stats ---")
    for key, value in engine.get_stats().items():
        print(f"  {key}: {value}")
