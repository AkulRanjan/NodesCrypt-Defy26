"""
CP6 Audit Logger
Generates tamper-proof incident hashes for INCO confidential logging.

What gets logged (confidentially via INCO):
- Decision hash
- Action taken
- Risk level
- Confidence score
- Timestamp

Never logged publicly:
- IPs, wallet balances, raw ML features, mempool contents
"""
import hashlib
import json
import time
from datetime import datetime

class IncidentLogger:
    def __init__(self):
        self.incidents = []
        
    def generate_incident(self, state, action, mode, confidence=0.0):
        """
        Generate a deterministic incident hash.
        
        Args:
            state: State vector [tx_count, avg_fee, congestion, spam_score, spam_ratio]
            action: RL action (0-3)
            mode: Mitigation mode string
            confidence: Model confidence score
            
        Returns:
            incident_id: SHA256 hash of the incident
            payload: Incident record (for INCO)
        """
        timestamp = int(time.time())
        
        # Create incident record (no sensitive data)
        payload = {
            "avg_spam_score": round(state[3], 4) if len(state) > 3 else 0,
            "congestion_score": round(state[2], 2) if len(state) > 2 else 0,
            "action_taken": int(action),
            "mitigation_mode": mode,
            "confidence": round(confidence, 4),
            "timestamp": timestamp,
            "timestamp_iso": datetime.utcfromtimestamp(timestamp).isoformat()
        }
        
        # Generate deterministic hash
        raw = json.dumps(payload, sort_keys=True).encode()
        incident_id = hashlib.sha256(raw).hexdigest()
        
        # Store locally for audit trail
        record = {
            "incident_id": incident_id,
            **payload
        }
        self.incidents.append(record)
        
        return incident_id, payload
    
    def get_incident(self, incident_id):
        """Retrieve incident by ID."""
        for inc in self.incidents:
            if inc["incident_id"] == incident_id:
                return inc
        return None
    
    def get_all_incidents(self):
        """Get all logged incidents."""
        return self.incidents
    
    def to_inco_format(self, incident_id, payload):
        """
        Format incident for INCO smart contract.
        Returns bytes32 hash and uint256 risk score.
        """
        # Convert hex string to bytes32 format
        incident_bytes32 = "0x" + incident_id
        
        # Calculate risk score (0-100 scale for uint256)
        risk_score = int(payload["avg_spam_score"] * 50 + 
                        (payload["congestion_score"] / 1e8) * 50)
        risk_score = min(100, max(0, risk_score))
        
        return {
            "incidentId": incident_bytes32,
            "actionTaken": payload["action_taken"],
            "riskScore": risk_score
        }


# Convenience functions
_logger = None

def get_logger():
    global _logger
    if _logger is None:
        _logger = IncidentLogger()
    return _logger

def generate_incident(state, action, mode, confidence=0.0):
    return get_logger().generate_incident(state, action, mode, confidence)


if __name__ == "__main__":
    # Test the logger
    print("=" * 60)
    print("[CP6] Audit Logger Test")
    print("=" * 60)
    
    logger = IncidentLogger()
    
    # Simulate some incidents
    test_cases = [
        ([5, 863364015, 4316820075, 0.25, 0.0], 3, "DEFENSIVE"),
        ([100, 1000, 5000, 0.8, 0.5], 2, "SPAM_DEPRIORITIZATION"),
        ([50, 500, 1000, 0.1, 0.1], 0, "NORMAL"),
    ]
    
    for state, action, mode in test_cases:
        incident_id, payload = logger.generate_incident(state, action, mode, confidence=0.95)
        print(f"\nState: {state[:3]}... Action: {action} Mode: {mode}")
        print(f"Incident ID: {incident_id[:16]}...")
        print(f"INCO Format: {logger.to_inco_format(incident_id, payload)}")
    
    print(f"\nTotal incidents logged: {len(logger.get_all_incidents())}")
