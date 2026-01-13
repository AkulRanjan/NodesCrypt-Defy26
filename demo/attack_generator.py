"""
Red Team Attack Generator
Generates attack scenarios for testing the checkpoint system.

Attack Types:
- Spam flood (low fee, high volume)
- Nonce flooding
- MEV sandwich patterns
- Large value transfers
- Approval exploits
"""
import random
import hashlib
import time
from typing import List, Dict, Generator
from datetime import datetime

class AttackGenerator:
    """Generates various attack patterns for testing."""
    
    def __init__(self):
        self.attack_count = 0
        
    def generate_spam_flood(self, count: int = 50, sender_count: int = 3) -> List[dict]:
        """
        Generate spam flood attack.
        Low fees, high volume from few senders.
        """
        txs = []
        senders = [f"0xspammer{i:04d}{'0' * 34}" for i in range(sender_count)]
        
        for i in range(count):
            txs.append({
                "hash": self._random_hash(),
                "from": random.choice(senders),
                "to": f"0xvictim{random.randint(1, 100):04d}{'0' * 34}",
                "value": str(random.randint(1, 100)),
                "gas_price": str(random.randint(100000, 1000000)),  # Very low
                "nonce": i,
                "data_size": random.randint(100, 500),
                "attack_type": "spam_flood"
            })
            self.attack_count += 1
        
        return txs
    
    def generate_nonce_flood(self, sender: str = None, count: int = 20) -> List[dict]:
        """
        Generate nonce flooding attack.
        Same sender, scattered nonces.
        """
        sender = sender or f"0xnonce_attacker{'0' * 26}"
        txs = []
        
        # Generate with gaps in nonces
        nonces = random.sample(range(1000), count)
        
        for nonce in nonces:
            txs.append({
                "hash": self._random_hash(),
                "from": sender,
                "to": f"0xtarget{'0' * 34}",
                "value": str(random.randint(100, 10000)),
                "gas_price": str(random.randint(10000000, 50000000)),
                "nonce": nonce,
                "data_size": 0,
                "attack_type": "nonce_flood"
            })
            self.attack_count += 1
        
        return txs
    
    def generate_mev_sandwich(self, victim_value: int = 10_000_000_000_000_000_000) -> List[dict]:
        """
        Generate MEV sandwich attack pattern.
        Front-run tx, victim tx, back-run tx.
        """
        attacker = f"0xmev_attacker{'0' * 28}"
        victim = f"0xvictim{'0' * 34}"
        
        txs = [
            # Front-run (high gas to get ahead)
            {
                "hash": self._random_hash(),
                "from": attacker,
                "to": f"0xdex{'0' * 36}",
                "value": str(victim_value // 2),
                "gas_price": str(100_000_000_000),  # 100 gwei
                "nonce": 1,
                "data_size": 68,
                "attack_type": "mev_front_run"
            },
            # Victim tx
            {
                "hash": self._random_hash(),
                "from": victim,
                "to": f"0xdex{'0' * 36}",
                "value": str(victim_value),
                "gas_price": str(50_000_000_000),  # 50 gwei
                "nonce": 1,
                "data_size": 68,
                "attack_type": "mev_victim"
            },
            # Back-run
            {
                "hash": self._random_hash(),
                "from": attacker,
                "to": f"0xdex{'0' * 36}",
                "value": str(victim_value // 2),
                "gas_price": str(40_000_000_000),  # 40 gwei
                "nonce": 2,
                "data_size": 68,
                "attack_type": "mev_back_run"
            }
        ]
        
        self.attack_count += 3
        return txs
    
    def generate_approval_exploit(self, count: int = 5) -> List[dict]:
        """
        Generate suspicious approval transactions.
        Unlimited approvals to unknown contracts.
        """
        txs = []
        
        for i in range(count):
            txs.append({
                "hash": self._random_hash(),
                "from": f"0xvictim{i:04d}{'0' * 34}",
                "to": f"0xmalicious_contract{'0' * 22}",
                "value": "0",
                "gas_price": str(random.randint(50_000_000_000, 100_000_000_000)),
                "nonce": random.randint(1, 100),
                "data": "0x095ea7b3" + "f" * 64,  # Approve signature + max amount
                "data_size": 68,
                "attack_type": "approval_exploit"
            })
            self.attack_count += 1
        
        return txs
    
    def generate_large_value_suspicious(self, count: int = 3) -> List[dict]:
        """
        Generate large value transfers from low reputation addresses.
        """
        txs = []
        
        for i in range(count):
            txs.append({
                "hash": self._random_hash(),
                "from": f"0xnew_address{i:04d}{'0' * 30}",
                "to": f"0xexchange{'0' * 32}",
                "value": str(random.randint(100, 10000) * 10**18),  # 100-10000 ETH
                "gas_price": str(random.randint(50_000_000_000, 100_000_000_000)),
                "nonce": 1,  # First tx ever = suspicious
                "data_size": 0,
                "attack_type": "large_value_new_address"
            })
            self.attack_count += 1
        
        return txs
    
    def generate_normal_traffic(self, count: int = 20) -> List[dict]:
        """
        Generate normal looking transactions for comparison.
        """
        txs = []
        
        for i in range(count):
            txs.append({
                "hash": self._random_hash(),
                "from": f"0xuser{random.randint(1, 10000):06d}{'0' * 28}",
                "to": f"0xmerchant{random.randint(1, 100):04d}{'0' * 30}",
                "value": str(random.randint(1, 10) * 10**17),  # 0.1-1 ETH
                "gas_price": str(random.randint(30_000_000_000, 60_000_000_000)),
                "nonce": random.randint(10, 500),
                "data_size": random.randint(0, 100),
                "attack_type": "normal"
            })
        
        return txs
    
    def generate_mixed_attack(self) -> List[dict]:
        """Generate a mix of attacks and normal traffic."""
        txs = []
        txs.extend(self.generate_normal_traffic(10))
        txs.extend(self.generate_spam_flood(20))
        txs.extend(self.generate_nonce_flood(count=5))
        txs.extend(self.generate_mev_sandwich())
        txs.extend(self.generate_approval_exploit(3))
        txs.extend(self.generate_large_value_suspicious(2))
        txs.extend(self.generate_normal_traffic(10))
        
        # Shuffle to mix
        random.shuffle(txs)
        return txs
    
    def _random_hash(self) -> str:
        """Generate a random transaction hash."""
        data = str(time.time()) + str(random.random())
        return "0x" + hashlib.sha256(data.encode()).hexdigest()
    
    def get_stats(self) -> dict:
        """Get attack generation statistics."""
        return {
            "total_attacks_generated": self.attack_count,
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    print("=" * 60)
    print("[RED TEAM] Attack Generator Test")
    print("=" * 60)
    
    generator = AttackGenerator()
    
    # Generate different attack types
    attacks = {
        "spam_flood": generator.generate_spam_flood(5),
        "nonce_flood": generator.generate_nonce_flood(count=3),
        "mev_sandwich": generator.generate_mev_sandwich(),
        "approval_exploit": generator.generate_approval_exploit(2),
        "large_value": generator.generate_large_value_suspicious(2)
    }
    
    for attack_type, txs in attacks.items():
        print(f"\n--- {attack_type.upper()} ({len(txs)} txs) ---")
        for tx in txs[:2]:  # Show first 2
            print(f"  Hash: {tx['hash'][:16]}...")
            print(f"  From: {tx['from'][:20]}...")
            print(f"  Value: {tx['value']}")
            print(f"  Gas: {tx['gas_price']}")
            print()
    
    print(f"\n--- Stats ---")
    print(generator.get_stats())
