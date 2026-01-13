"""
ETHIndia Demo Script - Attack Simulation
Simulates a spam attack to demonstrate checkpoint security response.
"""
import psycopg2
import random
import time
import hashlib

def connect_db():
    return psycopg2.connect(
        host="localhost",
        database="checkpoint",
        user="cp",
        password="cp"
    )

def generate_spam_tx():
    """Generate a spam-like transaction."""
    return {
        "hash": "0x" + hashlib.sha256(str(random.random()).encode()).hexdigest(),
        "sender": f"0xspammer{random.randint(1,5):04d}",
        "recipient": f"0xvictim{random.randint(1,100):04d}",
        "value": str(random.randint(1, 100)),
        "gas_price": str(random.randint(1, 10)),  # Low fee = spam
        "nonce": random.randint(1, 1000),
        "data_size": random.randint(100, 500),
    }

def generate_normal_tx():
    """Generate a normal transaction."""
    return {
        "hash": "0x" + hashlib.sha256(str(random.random()).encode()).hexdigest(),
        "sender": f"0xuser{random.randint(1,1000):04d}",
        "recipient": f"0xmerchant{random.randint(1,50):04d}",
        "value": str(random.randint(100, 10000)),
        "gas_price": str(random.randint(50, 200)),  # Normal fee
        "nonce": random.randint(1, 100),
        "data_size": random.randint(50, 200),
    }

def inject_transactions(conn, txs):
    """Insert transactions into mempool_txs."""
    cur = conn.cursor()
    for tx in txs:
        cur.execute("""
            INSERT INTO mempool_txs (hash, sender, recipient, value, gas_price, nonce, data_size)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (tx["hash"], tx["sender"], tx["recipient"], tx["value"], 
              tx["gas_price"], tx["nonce"], tx["data_size"]))
    conn.commit()
    cur.close()

def run_attack_demo():
    """Run the full attack simulation demo."""
    conn = connect_db()
    
    print("=" * 60)
    print("🎬 CHECKPOINT DEMO - SPAM ATTACK SIMULATION")
    print("=" * 60)
    
    # Phase 1: Normal traffic
    print("\n[PHASE 1] Normal traffic (5 seconds)...")
    for _ in range(10):
        inject_transactions(conn, [generate_normal_tx()])
    time.sleep(5)
    print("✓ Normal transactions injected")
    
    # Phase 2: Attack begins
    print("\n[PHASE 2] 🚨 SPAM ATTACK BEGINS!")
    print("Injecting 50 spam transactions...")
    for i in range(50):
        inject_transactions(conn, [generate_spam_tx()])
        if i % 10 == 0:
            print(f"  • Injected {i+10} spam txs")
    print("✓ Attack complete - watch the dashboard!")
    
    # Phase 3: Monitor response
    print("\n[PHASE 3] Observing checkpoint response...")
    print("Run: python mitigation/control_loop.py")
    print("Watch for DEFENSIVE_MODE activation")
    
    # Phase 4: Recovery
    print("\n[PHASE 4] Recovery with normal traffic")
    for _ in range(10):
        inject_transactions(conn, [generate_normal_tx()])
    print("✓ Normal traffic resumed")
    
    print("\n" + "=" * 60)
    print("🏁 DEMO COMPLETE")
    print("Key points to highlight:")
    print("  • Spam detected by CP3 (ML)")
    print("  • DEFENSIVE_MODE activated by CP4 (RL)")
    print("  • Fee threshold raised by CP5")
    print("  • Incident logged to INCO by CP6")
    print("  • Self-healing triggered by CP7")
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    run_attack_demo()
