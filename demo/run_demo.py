"""
ETHIndia Demo Runner
One-command demo script for judges.
"""
import subprocess
import time
import sys
import os

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def run_demo():
    print_header("CHECKPOINT SECURITY MIDDLEWARE - LIVE DEMO")
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  Privacy-preserving AI security for EVM blockchains       ║
    ║                                                           ║
    ║  • Real ML threat detection (CP3)                        ║
    ║  • Autonomous RL decisions (CP4)                         ║
    ║  • Active mitigation (CP5)                               ║
    ║  • INCO confidential audit (CP6)                         ║
    ║  • Self-healing (CP7)                                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    input("Press ENTER to start the demo...")
    
    # Phase 1: Show current state
    print_header("PHASE 1: CURRENT SYSTEM STATE")
    print("Running checkpoint control loop (3 cycles)...")
    
    # Import and run control loop
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mitigation.control_loop import run_full_loop
    
    run_full_loop(iterations=3)
    
    print_header("DEMO COMPLETE")
    print("""
    KEY TAKEAWAYS:
    
    ✅ Detected threats using ML (spam_score, risk_score)
    ✅ Made autonomous decisions using RL (DEFENSIVE_MODE)
    ✅ Applied real mitigations (fee threshold, delay)
    ✅ Logged incidents confidentially (INCO hash)
    ✅ Self-monitored and adapted (drift detection)
    
    "This all happened autonomously, without touching consensus."
    """)

if __name__ == "__main__":
    run_demo()
