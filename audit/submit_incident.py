"""
INCO Incident Submitter
Submit security incidents to the INCO SecurityAudit contract on-chain.

Usage:
    python audit/submit_incident.py --test  # Test with sample incident
    
Integration:
    from audit.submit_incident import submit_to_inco
    submit_to_inco(incident_id, action, risk_score)
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("[INCO] Warning: web3 not installed. Run: pip install web3")

# Load environment
from dotenv import load_dotenv
load_dotenv()

# INCO Network Config
INCO_RPC = os.getenv("INCO_RPC", "https://testnet.inco.org")
INCO_CHAIN_ID = 9090
INCO_CONTRACT_ADDRESS = os.getenv("INCO_CONTRACT_ADDRESS")

# SecurityAudit ABI (minimal)
SECURITY_AUDIT_ABI = [
    {
        "inputs": [
            {"name": "_incidentId", "type": "bytes32"},
            {"name": "_actionTaken", "type": "uint8"},
            {"name": "_riskScore", "type": "uint256"}
        ],
        "name": "logIncident",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalIncidents",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "_incidentId", "type": "bytes32"}],
        "name": "incidentExists",
        "outputs": [{"type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "incidentId", "type": "bytes32"},
            {"indexed": False, "name": "actionTaken", "type": "uint8"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "IncidentLogged",
        "type": "event"
    }
]


class IncoSubmitter:
    """Submit incidents to INCO SecurityAudit contract."""
    
    def __init__(self, private_key: str = None):
        if not WEB3_AVAILABLE:
            raise ImportError("web3 not available")
        
        self.w3 = Web3(Web3.HTTPProvider(INCO_RPC))
        
        # Add POA middleware for INCO
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Load private key
        self.private_key = private_key or os.getenv("PRIVATE_KEY")
        if self.private_key and not self.private_key.startswith("0x"):
            self.private_key = "0x" + self.private_key
        
        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)
            self.address = self.account.address
        else:
            self.account = None
            self.address = None
        
        # Load contract address
        self.contract_address = INCO_CONTRACT_ADDRESS
        if not self.contract_address:
            # Try to load from deployments.json
            deployments_path = Path(__file__).parent.parent / "deployments.json"
            if deployments_path.exists():
                with open(deployments_path) as f:
                    deployments = json.load(f)
                    if "inco" in deployments:
                        self.contract_address = deployments["inco"]["address"]
        
        if self.contract_address:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=SECURITY_AUDIT_ABI
            )
        else:
            self.contract = None
    
    def is_connected(self) -> bool:
        """Check if connected to INCO."""
        try:
            return self.w3.is_connected()
        except:
            return False
    
    def get_total_incidents(self) -> int:
        """Get total incidents logged on-chain."""
        if not self.contract:
            return 0
        try:
            return self.contract.functions.totalIncidents().call()
        except Exception as e:
            print(f"[INCO] Error getting total incidents: {e}")
            return 0
    
    def incident_exists(self, incident_id: bytes) -> bool:
        """Check if incident already logged."""
        if not self.contract:
            return False
        try:
            return self.contract.functions.incidentExists(incident_id).call()
        except:
            return False
    
    def submit_incident(
        self,
        incident_id: str | bytes,
        action: int,
        risk_score: int
    ) -> dict:
        """
        Submit incident to INCO on-chain.
        
        Args:
            incident_id: SHA256 hash of incident (hex string or bytes32)
            action: 0=PASS, 1=DELAY, 2=DROP, 3=ESCALATE
            risk_score: 0-100 scale
        
        Returns:
            Transaction receipt or error
        """
        if not self.contract:
            return {"error": "Contract not configured. Deploy first."}
        
        if not self.account:
            return {"error": "Private key not configured"}
        
        # Convert incident_id to bytes32
        if isinstance(incident_id, str):
            if incident_id.startswith("0x"):
                incident_id = bytes.fromhex(incident_id[2:])
            else:
                incident_id = bytes.fromhex(incident_id)
        
        # Pad to 32 bytes
        if len(incident_id) < 32:
            incident_id = incident_id.ljust(32, b'\0')
        elif len(incident_id) > 32:
            incident_id = incident_id[:32]
        
        try:
            # Check if already logged
            if self.incident_exists(incident_id):
                return {"status": "already_logged", "incident_id": incident_id.hex()}
            
            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.address)
            gas_price = self.w3.eth.gas_price
            
            tx = self.contract.functions.logIncident(
                incident_id,
                action,
                risk_score
            ).build_transaction({
                "chainId": INCO_CHAIN_ID,
                "from": self.address,
                "nonce": nonce,
                "gas": 100000,
                "gasPrice": gas_price
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            print(f"[INCO] Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            return {
                "status": "success",
                "tx_hash": receipt.transactionHash.hex(),
                "block": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
                "incident_id": incident_id.hex(),
                "explorer": f"https://explorer.inco.network/tx/{tx_hash.hex()}"
            }
            
        except Exception as e:
            return {"error": str(e)}


def generate_incident_id(payload: dict) -> str:
    """Generate deterministic incident ID from payload."""
    payload_str = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()


def submit_to_inco(incident_id: str, action: int, risk_score: int) -> dict:
    """
    Convenience function for submitting incidents.
    
    Usage:
        from audit.submit_incident import submit_to_inco
        result = submit_to_inco("abc123...", 2, 85)
    """
    try:
        submitter = IncoSubmitter()
        return submitter.submit_incident(incident_id, action, risk_score)
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="INCO Incident Submitter")
    parser.add_argument("--test", action="store_true", help="Submit test incident")
    parser.add_argument("--status", action="store_true", help="Check connection status")
    args = parser.parse_args()
    
    print("=" * 60)
    print("[INCO] Security Audit Submitter")
    print("=" * 60)
    
    try:
        submitter = IncoSubmitter()
        
        if args.status or not args.test:
            print(f"Connected to INCO: {submitter.is_connected()}")
            print(f"RPC: {INCO_RPC}")
            print(f"Contract: {submitter.contract_address or 'Not deployed'}")
            if submitter.address:
                print(f"Wallet: {submitter.address}")
                balance = submitter.w3.eth.get_balance(submitter.address)
                print(f"Balance: {Web3.from_wei(balance, 'ether')} INCO")
            if submitter.contract:
                print(f"Total incidents on-chain: {submitter.get_total_incidents()}")
        
        if args.test:
            print("\n[TEST] Submitting test incident...")
            
            # Generate test incident
            test_payload = {
                "action": 2,
                "mode": "DEFENSIVE",
                "spam_ratio": 0.75,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            incident_id = generate_incident_id(test_payload)
            print(f"Incident ID: {incident_id[:16]}...")
            
            result = submitter.submit_incident(
                incident_id=incident_id,
                action=2,  # DROP
                risk_score=75
            )
            
            print(f"\nResult: {json.dumps(result, indent=2)}")
            
    except ImportError as e:
        print(f"Error: {e}")
        print("Install web3: pip install web3 python-dotenv")
