"""
Transaction Simulator
Provides sandbox execution to detect malicious transactions before processing.

Features:
- Fork chain state for simulation
- Detect reverts, state changes, unusual behavior
- Estimate gas and MEV risk
- Cache simulation results
"""
import hashlib
import json
import time
from typing import Dict, Optional, List
from datetime import datetime

class SimulationResult:
    """Result of a transaction simulation."""
    
    def __init__(self):
        self.success = False
        self.reverted = False
        self.revert_reason = None
        self.gas_used = 0
        self.gas_estimate = 0
        self.state_changes = []
        self.logs = []
        self.value_transferred = 0
        self.risk_indicators = []
        self.simulation_time_ms = 0
        self.cached = False
        
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "reverted": self.reverted,
            "revert_reason": self.revert_reason,
            "gas_used": self.gas_used,
            "gas_estimate": self.gas_estimate,
            "state_change_count": len(self.state_changes),
            "log_count": len(self.logs),
            "value_transferred": self.value_transferred,
            "risk_indicators": self.risk_indicators,
            "simulation_time_ms": self.simulation_time_ms,
            "cached": self.cached
        }
    
    def get_risk_score(self) -> float:
        """Calculate risk score based on simulation results."""
        score = 0.0
        
        if self.reverted:
            score += 0.3
        
        if len(self.state_changes) > 10:
            score += 0.2
        
        if self.gas_used > 1_000_000:
            score += 0.1
            
        for indicator in self.risk_indicators:
            if indicator == "high_value_transfer":
                score += 0.2
            elif indicator == "unusual_gas":
                score += 0.1
            elif indicator == "multiple_calls":
                score += 0.1
                
        return min(1.0, score)


class SimulationCache:
    """Cache for simulation results."""
    
    def __init__(self, ttl_seconds=300):
        self.cache: Dict[str, SimulationResult] = {}
        self.ttl = ttl_seconds
        self.timestamps: Dict[str, float] = {}
        
    def _get_key(self, tx_data: dict) -> str:
        """Generate cache key from transaction data."""
        key_data = json.dumps({
            "from": tx_data.get("from", ""),
            "to": tx_data.get("to", ""),
            "data": tx_data.get("data", ""),
            "value": str(tx_data.get("value", 0))
        }, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def get(self, tx_data: dict) -> Optional[SimulationResult]:
        key = self._get_key(tx_data)
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                result = self.cache[key]
                result.cached = True
                return result
            del self.cache[key]
            del self.timestamps[key]
        return None
    
    def set(self, tx_data: dict, result: SimulationResult):
        key = self._get_key(tx_data)
        self.cache[key] = result
        self.timestamps[key] = time.time()


class TransactionSimulator:
    """
    Transaction simulation engine.
    Simulates transactions in a sandbox to detect risks.
    """
    
    def __init__(self, fork_url: str = None):
        self.fork_url = fork_url or "http://127.0.0.1:8545"
        self.cache = SimulationCache()
        self.simulation_count = 0
        self.cache_hits = 0
        
        # Risk thresholds
        self.high_value_threshold = 10_000_000_000_000_000_000  # 10 ETH in wei
        self.high_gas_threshold = 500_000
        
    def simulate(self, tx_data: dict, use_cache: bool = True) -> SimulationResult:
        """
        Simulate a transaction.
        
        Args:
            tx_data: Transaction data dict with from, to, value, data, gas
            use_cache: Whether to use cached results
            
        Returns:
            SimulationResult with risk analysis
        """
        # Check cache first
        if use_cache:
            cached = self.cache.get(tx_data)
            if cached:
                self.cache_hits += 1
                return cached
        
        self.simulation_count += 1
        start_time = time.time()
        result = SimulationResult()
        
        try:
            # Simulate the transaction (mock implementation)
            result = self._run_simulation(tx_data)
            
        except Exception as e:
            result.success = False
            result.reverted = True
            result.revert_reason = str(e)
            result.risk_indicators.append("simulation_error")
        
        result.simulation_time_ms = int((time.time() - start_time) * 1000)
        
        # Cache the result
        if use_cache:
            self.cache.set(tx_data, result)
        
        return result
    
    def _run_simulation(self, tx_data: dict) -> SimulationResult:
        """
        Run actual simulation (mock implementation).
        In production, this would fork the chain and execute.
        """
        result = SimulationResult()
        result.success = True
        
        # Analyze transaction data for risk indicators
        value = int(tx_data.get("value", 0))
        gas = int(tx_data.get("gas", 21000))
        data = tx_data.get("data", "")
        
        # Check for high value
        if value > self.high_value_threshold:
            result.risk_indicators.append("high_value_transfer")
            result.value_transferred = value
            
        # Check for complex data (potential contract interaction)
        if data and len(data) > 10:
            result.risk_indicators.append("contract_interaction")
            
            # Check for common exploit signatures
            if data.startswith("0xa9059cbb"):  # ERC20 transfer
                result.risk_indicators.append("token_transfer")
            elif data.startswith("0x095ea7b3"):  # ERC20 approve
                result.risk_indicators.append("approval")
                result.risk_indicators.append("potential_drain_risk")
                
        # Check gas usage
        if gas > self.high_gas_threshold:
            result.risk_indicators.append("high_gas")
            result.gas_estimate = gas
            
        # Simulate gas used (mock)
        result.gas_used = min(gas, 100000)
        
        # Mock state changes based on data complexity
        if data:
            result.state_changes = [{"type": "storage", "count": len(data) // 64}]
            
        return result
    
    def simulate_batch(self, transactions: List[dict]) -> List[SimulationResult]:
        """Simulate multiple transactions."""
        return [self.simulate(tx) for tx in transactions]
    
    def get_stats(self) -> dict:
        """Get simulator statistics."""
        return {
            "simulation_count": self.simulation_count,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / max(1, self.simulation_count + self.cache_hits),
            "cache_size": len(self.cache.cache)
        }
    
    def should_simulate(self, tx_data: dict, spam_score: float = 0.0) -> bool:
        """
        Determine if a transaction should be simulated.
        Simulation is expensive, so we only simulate high-risk txs.
        """
        value = int(tx_data.get("value", 0))
        data = tx_data.get("data", "")
        
        # Simulate if high value
        if value > self.high_value_threshold / 10:  # 1 ETH threshold
            return True
            
        # Simulate if complex contract call
        if data and len(data) > 100:
            return True
            
        # Simulate if ML flagged as risky
        if spam_score > 0.7:
            return True
            
        return False


# Singleton instance
_simulator = None

def get_simulator() -> TransactionSimulator:
    global _simulator
    if _simulator is None:
        _simulator = TransactionSimulator()
    return _simulator

def simulate_tx(tx_data: dict) -> SimulationResult:
    """Convenience function for transaction simulation."""
    return get_simulator().simulate(tx_data)


if __name__ == "__main__":
    print("=" * 60)
    print("[SIMULATOR] Transaction Simulator Test")
    print("=" * 60)
    
    sim = TransactionSimulator()
    
    # Test transactions
    test_txs = [
        {
            "from": "0xuser1",
            "to": "0xcontract1",
            "value": 1000000000000000000,  # 1 ETH
            "data": "0xa9059cbb000000000000000000000000recipient00000000000000000000000000000000000000000000000000000000000000000000000000de0b6b3a7640000",
            "gas": 100000
        },
        {
            "from": "0xuser2",
            "to": "0xcontract2",
            "value": 50000000000000000000000,  # 50000 ETH
            "data": "0x095ea7b3",  # Approve
            "gas": 50000
        },
        {
            "from": "0xuser3",
            "to": "0xwallet",
            "value": 100000000000000000,  # 0.1 ETH
            "data": "",
            "gas": 21000
        }
    ]
    
    for i, tx in enumerate(test_txs):
        print(f"\n--- Transaction {i+1} ---")
        result = sim.simulate(tx)
        print(f"Success: {result.success}")
        print(f"Risk Score: {result.get_risk_score():.2f}")
        print(f"Risk Indicators: {result.risk_indicators}")
        print(f"Simulation Time: {result.simulation_time_ms}ms")
    
    print(f"\n--- Stats ---")
    print(sim.get_stats())
