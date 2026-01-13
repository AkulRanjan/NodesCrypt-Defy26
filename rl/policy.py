from stable_baselines3 import PPO
import numpy as np
import os

# Get the path to the model file
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, "checkpoint_rl_policy")

model = PPO.load(model_path)

ACTION_NAMES = {
    0: "DO_NOTHING",
    1: "RAISE_FEE_THRESHOLD",
    2: "DEPRIORITIZE_SPAM",
    3: "DEFENSIVE_MODE"
}

def decide_action(state):
    """
    Given a state vector, return the RL-decided action.
    
    State format:
    [mempool_tx_count, avg_fee_rate, congestion_score, avg_spam_score, spam_tx_ratio]
    """
    action, _ = model.predict(np.array(state, dtype=np.float32), deterministic=True)
    return int(action)

def decide_action_with_name(state):
    """
    Returns both the action ID and human-readable name.
    """
    action = decide_action(state)
    return action, ACTION_NAMES[action]

if __name__ == "__main__":
    # Test with sample states
    test_states = [
        [50, 0.001, 100, 0.1, 0.1],   # Low congestion
        [150, 0.01, 500, 0.8, 0.7],   # High congestion, high spam
        [100, 0.005, 300, 0.5, 0.4],  # Medium state
    ]
    
    print("[CP4] Policy Inference Test")
    print("-" * 50)
    for state in test_states:
        action, name = decide_action_with_name(state)
        print(f"State: {state}")
        print(f"Action: {action} ({name})")
        print()
