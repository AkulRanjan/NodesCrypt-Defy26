"""
Nodescrypt EVM Feature Extractor
Production-grade feature engineering for Ethereum transactions

Features:
- Contract detection with caching
- ERC20/ERC721 decode
- MEV risk features
- Sender history analysis
- Nonce gap detection
"""
import os
import sys
import time
import json
import hashlib
import psycopg2
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from collections import defaultdict

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
ETH_RPC = os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "checkpoint")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cp")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cp")

# Try to import metrics
try:
    from monitoring.metrics_exporter import record_spam_detected
    METRICS_AVAILABLE = True
except:
    METRICS_AVAILABLE = False
    def record_spam_detected(score): pass


class ContractCache:
    """Cache for eth_getCode results."""
    
    def __init__(self, max_size=50000):
        self.cache = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, address: str) -> Optional[bool]:
        if address in self.cache:
            self.hits += 1
            return self.cache[address]
        self.misses += 1
        return None
    
    def set(self, address: str, is_contract: bool):
        if len(self.cache) >= self.max_size:
            # Evict oldest 20%
            keys_to_remove = list(self.cache.keys())[:self.max_size // 5]
            for k in keys_to_remove:
                del self.cache[k]
        self.cache[address] = is_contract


class EVMFeatureExtractor:
    """
    Production-grade EVM feature extractor.
    """
    
    def __init__(self):
        self.rpc_url = ETH_RPC
        self.conn = None
        self.contract_cache = ContractCache()
        self.sender_history = defaultdict(list)
        self.nonce_cache = {}
        
        # Stats
        self.features_extracted = 0
        self.rpc_calls = 0
        
        # Common function selectors
        self.SELECTORS = {
            "0xa9059cbb": "transfer",
            "0x095ea7b3": "approve",
            "0x23b872dd": "transferFrom",
            "0x42842e0e": "safeTransferFrom",
            "0x38ed1739": "swapExactTokensForTokens",
            "0x7ff36ab5": "swapExactETHForTokens",
            "0x791ac947": "swapExactTokensForETHSupportingFeeOnTransferTokens",
            "0xfb3bdb41": "swapETHForExactTokens",
            "0x5c11d795": "swapExactTokensForTokensSupportingFeeOnTransferTokens"
        }
        
        # DEX router addresses (Uniswap, Sushiswap, etc.)
        self.DEX_ROUTERS = {
            "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "UniswapV2",
            "0xe592427a0aece92de3edee1f18e0157c05861564": "UniswapV3",
            "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": "Sushiswap",
            "0x881d40237659c251811cec9c364ef91dc08d300c": "Metamask"
        }
    
    def connect_db(self):
        """Connect to PostgreSQL."""
        try:
            self.conn = psycopg2.connect(
                host=POSTGRES_HOST,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            print("[EVM-FEATURES] Connected to PostgreSQL")
            return True
        except Exception as e:
            print(f"[EVM-FEATURES] DB error: {e}")
            return False
    
    def eth_call(self, method: str, params: list) -> Optional[dict]:
        """Make ETH RPC call."""
        try:
            self.rpc_calls += 1
            response = requests.post(
                self.rpc_url,
                json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
                timeout=10
            )
            result = response.json()
            return result.get("result")
        except:
            return None
    
    def is_contract(self, address: str) -> bool:
        """Check if address is a contract."""
        if not address:
            return False
        
        address = address.lower()
        cached = self.contract_cache.get(address)
        if cached is not None:
            return cached
        
        code = self.eth_call("eth_getCode", [address, "latest"])
        is_contr = code is not None and code != "0x"
        self.contract_cache.set(address, is_contr)
        return is_contr
    
    def get_chain_nonce(self, address: str) -> int:
        """Get on-chain nonce for address."""
        if not address:
            return 0
        
        address = address.lower()
        # Cache for 10 seconds
        cache_key = address
        if cache_key in self.nonce_cache:
            cached_time, cached_nonce = self.nonce_cache[cache_key]
            if time.time() - cached_time < 10:
                return cached_nonce
        
        result = self.eth_call("eth_getTransactionCount", [address, "latest"])
        if result:
            nonce = int(result, 16)
            self.nonce_cache[cache_key] = (time.time(), nonce)
            return nonce
        return 0
    
    def decode_function(self, data: str) -> dict:
        """Decode function call from input data."""
        if not data or len(data) < 10:
            return {"function": "transfer", "is_swap": False}
        
        selector = data[:10].lower()
        func_name = self.SELECTORS.get(selector, "unknown")
        is_swap = "swap" in func_name.lower()
        
        return {
            "function": func_name,
            "selector": selector,
            "is_swap": is_swap,
            "is_approve": func_name == "approve",
            "is_transfer": func_name in ["transfer", "transferFrom"]
        }
    
    def get_mev_risk_score(self, tx: dict, func_info: dict) -> float:
        """Calculate MEV risk score."""
        score = 0.0
        
        # Swap transactions are MEV targets
        if func_info.get("is_swap"):
            score += 0.4
        
        # High value swaps
        value = int(tx.get("value", "0"))
        if value > 1e18:  # > 1 ETH
            score += 0.2
        if value > 10e18:  # > 10 ETH
            score += 0.2
        
        # Transaction to DEX router
        recipient = (tx.get("recipient") or tx.get("to", "")).lower()
        if recipient in self.DEX_ROUTERS:
            score += 0.2
        
        # Large input data (complex swap)
        data_size = tx.get("data_size", 0)
        if data_size > 200:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_sender_features(self, sender: str) -> dict:
        """Get sender history features."""
        history = self.sender_history.get(sender, [])
        now = time.time()
        
        # Filter to last 60 seconds
        recent = [t for t in history if now - t < 60]
        self.sender_history[sender] = recent[-100:]  # Keep last 100
        
        return {
            "sender_tx_count_1m": len(recent),
            "sender_is_new": len(recent) == 0,
            "sender_burst": len(recent) > 10
        }
    
    def safe_int(self, value, default=0):
        """Safely convert value to int."""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def safe_float(self, value, default=0.0):
        """Safely convert value to float."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def extract_features(self, tx: dict) -> dict:
        """Extract full feature set for a transaction."""
        # Basic features with safe conversion
        value = self.safe_float(tx.get("value", 0))
        gas_price = self.safe_float(tx.get("gas_price", 0))
        
        features = {
            "hash": tx.get("hash", ""),
            "sender": tx.get("sender", tx.get("from", "")) or "",
            "recipient": tx.get("recipient", tx.get("to", "")) or "",
            
            # Value features
            "value": value,
            "value_eth": value / 1e18 if value else 0,
            
            # Gas features
            "gas_price": gas_price,
            "gas_price_gwei": gas_price / 1e9 if gas_price else 0,
            "gas_limit": self.safe_int(tx.get("gas_limit"), 21000),
            "max_fee_per_gas": self.safe_float(tx.get("max_fee_per_gas")),
            "max_priority_fee": self.safe_float(tx.get("max_priority_fee_per_gas")),
            
            # Data features
            "data_size": self.safe_int(tx.get("data_size")),
            "nonce": self.safe_int(tx.get("nonce")),
            "tx_type": self.safe_int(tx.get("tx_type")),
            
            # Contract detection
            "to_is_contract": self.is_contract(tx.get("recipient") or tx.get("to")),
            "is_contract_creation": not tx.get("recipient") and not tx.get("to"),
        }
        
        # Function decode
        data = tx.get("data", tx.get("input", "0x"))
        func_info = self.decode_function(data)
        features.update({
            "function_name": func_info["function"],
            "is_swap": func_info["is_swap"],
            "is_approve": func_info.get("is_approve", False),
            "is_token_transfer": func_info.get("is_transfer", False)
        })
        
        # Nonce gap
        chain_nonce = self.get_chain_nonce(features["sender"])
        features["nonce_gap"] = features["nonce"] - chain_nonce
        
        # Sender features
        sender = features["sender"]
        sender_features = self.get_sender_features(sender)
        features.update(sender_features)
        
        # Record sender activity
        if sender:
            self.sender_history[sender].append(time.time())
        
        # MEV risk
        features["mev_risk_score"] = self.get_mev_risk_score(tx, func_info)
        
        # Spam indicators
        features["spam_indicators"] = 0
        if features["gas_price_gwei"] < 1:
            features["spam_indicators"] += 1
        if features["sender_tx_count_1m"] > 5:
            features["spam_indicators"] += 1
        if features["nonce_gap"] > 10:
            features["spam_indicators"] += 1
        if features["data_size"] > 1000:
            features["spam_indicators"] += 1
        
        # Spam score (heuristic)
        features["spam_score"] = min(features["spam_indicators"] / 4.0, 1.0)
        
        self.features_extracted += 1
        return features
    
    def save_features(self, features: dict) -> bool:
        """Save features to database."""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO tx_features (
                    hash, fee_rate, value, data_size, nonce_gap,
                    sender_tx_count, sender_avg_fee, first_seen,
                    to_is_contract, is_swap, mev_risk_score, spam_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hash) DO NOTHING
            """, (
                features["hash"],
                features["gas_price_gwei"],
                features["value_eth"],
                features["data_size"],
                features["nonce_gap"],
                features["sender_tx_count_1m"],
                features["gas_price_gwei"],
                datetime.utcnow(),
                features["to_is_contract"],
                features["is_swap"],
                features["mev_risk_score"],
                features["spam_score"]
            ))
            self.conn.commit()
            cur.close()
            
            # Record metrics
            if METRICS_AVAILABLE:
                record_spam_detected(features["spam_score"])
            
            return True
        except Exception as e:
            self.conn.rollback()
            return False
    
    def process_pending_txs(self):
        """Process unprocessed transactions."""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT hash, sender, recipient, value, gas_price, nonce, data_size,
                       gas_limit, max_fee_per_gas, max_priority_fee_per_gas, tx_type
                FROM mempool_txs
                WHERE hash NOT IN (SELECT hash FROM tx_features)
                ORDER BY first_seen DESC
                LIMIT 100
            """)
            rows = cur.fetchall()
            cur.close()
            
            for row in rows:
                tx = {
                    "hash": row[0],
                    "sender": row[1],
                    "recipient": row[2],
                    "value": row[3],
                    "gas_price": row[4],
                    "nonce": row[5],
                    "data_size": row[6],
                    "gas_limit": row[7],
                    "max_fee_per_gas": row[8],
                    "max_priority_fee_per_gas": row[9],
                    "tx_type": row[10]
                }
                
                features = self.extract_features(tx)
                self.save_features(features)
            
            return len(rows)
            
        except Exception as e:
            print(f"[EVM-FEATURES] Error: {e}")
            return 0
    
    def run(self):
        """Main extraction loop."""
        print("=" * 60)
        print("[EVM-FEATURES] Nodescrypt Feature Extractor")
        print("=" * 60)
        
        if not self.connect_db():
            return
        
        print("[EVM-FEATURES] Starting extraction loop...")
        
        while True:
            try:
                processed = self.process_pending_txs()
                if processed > 0:
                    print(f"[EVM-FEATURES] Processed {processed} txs (total: {self.features_extracted})")
                time.sleep(2)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[EVM-FEATURES] Error: {e}")
                time.sleep(5)
        
        print(f"\n[EVM-FEATURES] Final stats: features={self.features_extracted}, rpc_calls={self.rpc_calls}")


if __name__ == "__main__":
    extractor = EVMFeatureExtractor()
    extractor.run()
