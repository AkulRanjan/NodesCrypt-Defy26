"""
Threat Intelligence Service
Provides reputation lookup, blacklist checking, and risk scoring for addresses.

Features:
- Local blacklist cache (fast lookup)
- Reputation scoring
- Integration with external APIs (Etherscan, public scam lists)
- Feature enrichment for ML
"""
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import os

class ReputationCache:
    """In-memory cache for address reputation data."""
    
    def __init__(self, ttl_seconds=3600):
        self.cache: Dict[str, dict] = {}
        self.ttl = ttl_seconds
        
    def get(self, address: str) -> Optional[dict]:
        address = address.lower()
        if address in self.cache:
            entry = self.cache[address]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["data"]
            del self.cache[address]
        return None
    
    def set(self, address: str, data: dict):
        address = address.lower()
        self.cache[address] = {
            "data": data,
            "timestamp": time.time()
        }
        
    def clear(self):
        self.cache.clear()


class ThreatIntelligence:
    """
    Main threat intelligence service.
    Provides address reputation, blacklist lookup, and risk scoring.
    """
    
    def __init__(self):
        self.cache = ReputationCache(ttl_seconds=3600)
        self.blacklist: set = set()
        self.whitelist: set = set()
        self.known_entities: Dict[str, dict] = {}
        self._load_local_lists()
        
    def _load_local_lists(self):
        """Load local blacklist/whitelist from files."""
        # Known scam addresses (sample)
        self.blacklist = {
            "0xbad0000000000000000000000000000000000001",
            "0xbad0000000000000000000000000000000000002",
            "0xscammer000000000000000000000000000001",
        }
        
        # Known legitimate addresses
        self.whitelist = {
            "0x0000000000000000000000000000000000000000",  # Null address
        }
        
        # Known entities with metadata
        self.known_entities = {
            "0x0000000000000000000000000000000000000000": {
                "name": "Null Address",
                "category": "system",
                "risk": 0
            }
        }
    
    def add_to_blacklist(self, address: str, reason: str = "manual"):
        """Add address to local blacklist."""
        self.blacklist.add(address.lower())
        self.cache.set(address, {
            "is_blacklisted": True,
            "reason": reason,
            "source": "local"
        })
        
    def add_to_whitelist(self, address: str):
        """Add address to local whitelist."""
        self.whitelist.add(address.lower())
        
    def lookup(self, address: str) -> dict:
        """
        Lookup address reputation.
        Returns reputation data with risk scoring.
        """
        address = address.lower()
        
        # Check cache first
        cached = self.cache.get(address)
        if cached:
            return cached
        
        # Build reputation profile
        result = {
            "address": address,
            "is_blacklisted": address in self.blacklist,
            "is_whitelisted": address in self.whitelist,
            "reputation_score": 0.5,  # Neutral default
            "risk_level": "UNKNOWN",
            "entity": self.known_entities.get(address),
            "first_seen": None,
            "sources": ["local"],
            "tags": [],
            "lookup_time": datetime.utcnow().isoformat()
        }
        
        # Calculate risk score
        if result["is_blacklisted"]:
            result["reputation_score"] = 0.0
            result["risk_level"] = "CRITICAL"
            result["tags"].append("blacklisted")
        elif result["is_whitelisted"]:
            result["reputation_score"] = 1.0
            result["risk_level"] = "SAFE"
            result["tags"].append("whitelisted")
        elif result["entity"]:
            result["reputation_score"] = 1.0 - (result["entity"].get("risk", 0.5))
            result["risk_level"] = "KNOWN"
            result["tags"].append(result["entity"].get("category", "entity"))
        else:
            # Unknown address - neutral risk
            result["reputation_score"] = 0.5
            result["risk_level"] = "UNKNOWN"
        
        # Cache result
        self.cache.set(address, result)
        return result
    
    def batch_lookup(self, addresses: List[str]) -> Dict[str, dict]:
        """Lookup multiple addresses at once."""
        return {addr: self.lookup(addr) for addr in addresses}
    
    def get_features(self, address: str) -> dict:
        """
        Get ML-ready features for an address.
        Returns numeric features for model input.
        """
        rep = self.lookup(address)
        return {
            "is_blacklisted": 1 if rep["is_blacklisted"] else 0,
            "is_whitelisted": 1 if rep["is_whitelisted"] else 0,
            "reputation_score": rep["reputation_score"],
            "is_known_entity": 1 if rep["entity"] else 0,
            "risk_numeric": {
                "SAFE": 0, "KNOWN": 0.2, "UNKNOWN": 0.5, "HIGH": 0.8, "CRITICAL": 1.0
            }.get(rep["risk_level"], 0.5)
        }
    
    def update_from_external(self, address: str, external_data: dict):
        """Update cache with external API data."""
        cached = self.cache.get(address) or {}
        cached.update(external_data)
        cached["sources"] = list(set(cached.get("sources", []) + ["external"]))
        self.cache.set(address, cached)
        return cached


# Singleton instance
_intel = None

def get_intel() -> ThreatIntelligence:
    global _intel
    if _intel is None:
        _intel = ThreatIntelligence()
    return _intel

def lookup_address(address: str) -> dict:
    """Convenience function for address lookup."""
    return get_intel().lookup(address)

def get_address_features(address: str) -> dict:
    """Convenience function for ML features."""
    return get_intel().get_features(address)


if __name__ == "__main__":
    print("=" * 60)
    print("[THREAT INTEL] Service Test")
    print("=" * 60)
    
    intel = ThreatIntelligence()
    
    # Test addresses
    test_addresses = [
        "0xbad0000000000000000000000000000000000001",  # Blacklisted
        "0x0000000000000000000000000000000000000000",  # Whitelisted
        "0xuser1234567890abcdef1234567890abcdef1234",  # Unknown
    ]
    
    for addr in test_addresses:
        rep = intel.lookup(addr)
        features = intel.get_features(addr)
        print(f"\nAddress: {addr[:20]}...")
        print(f"  Risk Level: {rep['risk_level']}")
        print(f"  Reputation: {rep['reputation_score']}")
        print(f"  Blacklisted: {rep['is_blacklisted']}")
        print(f"  ML Features: {features}")
