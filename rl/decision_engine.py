"""
Real-time RL Decision Engine that connects CP2 features, CP3 ML scores, and RL policy.
"""
import psycopg2
import requests
import numpy as np
import sys
import os

# Add rl directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rl'))
from policy import decide_action_with_name, ACTION_NAMES

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="checkpoint",
    user="cp",
    password="cp"
)

ML_SERVICE_URL = "http://127.0.0.1:8002"

def get_mempool_state():
    """Get current mempool state from CP2 features."""
    cur = conn.cursor()
    
    # Get latest mempool snapshot
    cur.execute("""
        SELECT tx_count, avg_fee_rate, congestion_score
        FROM mempool_features
        ORDER BY snapshot_time DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    
    if row:
        return {
            "tx_count": row[0],
            "avg_fee_rate": row[1],
            "congestion_score": row[2]
        }
    return None

def get_avg_spam_score():
    """Get average spam score from CP3 ML service for recent transactions."""
    cur = conn.cursor()
    
    # Get recent transactions for spam scoring
    cur.execute("""
        SELECT fee_rate, data_size, nonce_gap, sender_tx_count, sender_avg_fee
        FROM tx_features
        ORDER BY first_seen DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    cur.close()
    
    if not rows:
        return 0.5, 0.0  # Default values
    
    spam_scores = []
    for row in rows:
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/predict/spam",
                json={
                    "fee_rate": float(row[0]),
                    "data_size": int(row[1]),
                    "nonce_gap": int(row[2]),
                    "sender_tx_count": int(row[3]),
                    "sender_avg_fee": float(row[4])
                }
            )
            if response.status_code == 200:
                spam_scores.append(response.json()["spam_score"])
        except:
            pass
    
    if spam_scores:
        avg_spam = np.mean(spam_scores)
        spam_ratio = len([s for s in spam_scores if s > 0.5]) / len(spam_scores)
        return avg_spam, spam_ratio
    
    return 0.5, 0.0

def build_state_vector():
    """Build the RL state vector from CP2 and CP3 outputs."""
    mempool = get_mempool_state()
    avg_spam, spam_ratio = get_avg_spam_score()
    
    if mempool is None:
        print("[CP4] Warning: No mempool data available")
        return None
    
    state = [
        mempool["tx_count"],
        mempool["avg_fee_rate"],
        mempool["congestion_score"],
        avg_spam,
        spam_ratio
    ]
    
    return state

def run_decision_engine():
    """Run one decision cycle."""
    state = build_state_vector()
    
    if state is None:
        return None, None
    
    action, action_name = decide_action_with_name(state)
    
    print(f"[CP4] State: tx_count={state[0]}, avg_fee={state[1]:.6f}, "
          f"congestion={state[2]:.2f}, spam_score={state[3]:.2f}, spam_ratio={state[4]:.2f}")
    print(f"[CP4] RL decided action = {action_name}")
    
    return action, action_name

if __name__ == "__main__":
    print("[CP4] RL Decision Engine - Real Data Test")
    print("=" * 60)
    action, name = run_decision_engine()
    if action is not None:
        print(f"\nFinal Decision: {name}")
