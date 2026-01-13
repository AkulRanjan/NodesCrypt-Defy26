"""
CP5+CP6+CP7 Full Control Loop
Integrates mitigation, audit logging, and self-monitoring.
"""
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mitigation.engine import MitigationEngine
from rl.decision_engine import build_state_vector
from audit.logger import IncidentLogger
from monitoring.collector import MetricsCollector
from monitoring.drift import DriftDetector
from monitoring.heal import SelfHealer

# Import RL policy
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rl'))
from policy import decide_action_with_name

# Initialize all components
engine = MitigationEngine()
logger = IncidentLogger()
metrics = MetricsCollector()
drift_detector = DriftDetector()
healer = SelfHealer(engine)

def run_full_loop(iterations=None):
    """
    Full control loop with all checkpoints:
    - CP2/CP3: Get state and ML scores
    - CP4: RL decides action
    - CP5: Apply mitigation
    - CP6: Log to INCO
    - CP7: Monitor, detect drift, self-heal
    """
    print("=" * 60)
    print("[CP1-CP7] FULL AUTONOMOUS SECURITY LOOP")
    print("=" * 60)
    print()
    
    i = 0
    while iterations is None or i < iterations:
        i += 1
        print(f"\n{'='*60}")
        print(f"[CYCLE {i}]")
        print(f"{'='*60}")
        
        # CP2/CP3: Get state
        state = build_state_vector()
        if state is None:
            print("[ERROR] Could not build state vector")
            time.sleep(5)
            continue
        
        # Display compact state
        print(f"[STATE] tx={state[0]}, spam={state[3]:.2f}, congestion={state[2]:.0f}")
        
        # CP4: RL decision (check if frozen by CP7)
        if healer.is_rl_frozen():
            action, action_name = 0, "DO_NOTHING (RL FROZEN)"
            print(f"[CP4] ⚠️ RL FROZEN - using safe fallback")
        else:
            action, action_name = decide_action_with_name(state)
        print(f"[CP4] Decision: {action} ({action_name})")
        
        # CP5: Apply mitigation
        engine.apply(action)
        
        # CP6: INCO audit log
        incident_id, payload = logger.generate_incident(
            state=state, action=action, mode=engine.mode, confidence=0.95
        )
        inco_data = logger.to_inco_format(incident_id, payload)
        print(f"[CP6] 🔐 Incident: {incident_id[:12]}... Risk: {inco_data['riskScore']}")
        
        # CP7: Collect metrics
        reward = -state[0] * 0.01 - state[4] * 10  # Same as RL reward
        metrics.update(
            mempool_tx_count=state[0],
            spam_ratio=state[4],
            spam_score=state[3],
            false_positive=0.05,  # Simulated
            reward=reward,
            action=action,
            risk_score=inco_data['riskScore'],
            model_confidence=0.95
        )
        
        # CP7: Detect drift
        summary = metrics.summary()
        alerts = drift_detector.detect(summary)
        
        if alerts:
            print(f"[CP7] 🚨 DRIFT ALERTS:")
            for alert in alerts:
                print(f"      [{alert['severity']}] {alert['type']}")
            
            # Self-heal
            healing_actions = healer.heal(alerts)
            if healing_actions:
                print(f"[CP7] 🔧 HEALING: {[a['action'] for a in healing_actions]}")
        else:
            print(f"[CP7] ✓ No drift detected")
        
        # Status summary
        status = engine.get_status()
        print(f"\n[STATUS] Mode: {status['mode']} | Fee: {status['min_fee']} gwei")
        print(f"         Samples: {summary['samples_collected']} | Avg Reward: {summary['avg_reward']:.2f}")
        
        if iterations is None:
            time.sleep(5)
    
    # Final summary
    print("\n" + "=" * 60)
    print("[FINAL SUMMARY]")
    print("=" * 60)
    print(f"Incidents logged: {len(logger.get_all_incidents())}")
    print(f"Metrics collected: {metrics.summary()['samples_collected']}")
    print(f"Healing actions: {len(healer.get_healing_history())}")
    print(f"RL Frozen: {healer.is_rl_frozen()}")


if __name__ == "__main__":
    run_full_loop(iterations=5)
