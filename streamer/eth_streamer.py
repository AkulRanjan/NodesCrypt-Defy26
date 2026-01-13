"""
Live Ethereum Transaction Streamer
Connects to Ethereum RPC and streams pending transactions into PostgreSQL.

This is the REAL data source that feeds the entire Checkpoint pipeline.
"""
import os
import sys
import time
import json
import psycopg2
import requests
from datetime import datetime
from typing import Dict, Optional
import threading
from concurrent.futures import ThreadPoolExecutor

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
ETH_RPC_URL = os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "checkpoint")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cp")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cp")

# Try to import metrics
try:
    from monitoring.metrics_exporter import record_transaction_received
    METRICS_AVAILABLE = True
except:
    METRICS_AVAILABLE = False
    def record_transaction_received(): pass


class EthereumStreamer:
    """
    Streams live Ethereum transactions from mempool.
    """
    
    def __init__(self, rpc_url: str = None):
        self.rpc_url = rpc_url or ETH_RPC_URL
        self.conn = None
        self.running = False
        self.tx_count = 0
        self.error_count = 0
        self.last_block = 0
        self.seen_hashes = set()
        self.max_seen_cache = 10000
        
        print(f"[STREAMER] Initialized with RPC: {self.rpc_url[:50]}...")
        
    def connect_db(self):
        """Connect to PostgreSQL."""
        try:
            self.conn = psycopg2.connect(
                host=POSTGRES_HOST,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            print("[STREAMER] Connected to PostgreSQL")
            return True
        except Exception as e:
            print(f"[STREAMER] DB connection failed: {e}")
            return False
    
    def eth_rpc_call(self, method: str, params: list = None) -> Optional[dict]:
        """Make an Ethereum JSON-RPC call."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or [],
                "id": 1
            }
            response = requests.post(
                self.rpc_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            result = response.json()
            if "error" in result:
                return None
            return result.get("result")
        except Exception as e:
            self.error_count += 1
            return None
    
    def get_pending_transactions(self) -> list:
        """Get pending transactions from mempool."""
        # Method 1: txpool_content (works with some nodes)
        result = self.eth_rpc_call("txpool_content")
        if result:
            txs = []
            for status in ["pending", "queued"]:
                if status in result:
                    for sender, nonce_txs in result[status].items():
                        for nonce, tx in nonce_txs.items():
                            txs.append(tx)
            return txs
        
        # Method 2: eth_getBlockByNumber for latest block
        result = self.eth_rpc_call("eth_getBlockByNumber", ["pending", True])
        if result and "transactions" in result:
            return result["transactions"]
        
        return []
    
    def get_latest_block_transactions(self) -> list:
        """Get transactions from the latest block."""
        result = self.eth_rpc_call("eth_getBlockByNumber", ["latest", True])
        if result and "transactions" in result:
            block_num = int(result["number"], 16)
            if block_num > self.last_block:
                self.last_block = block_num
                return result["transactions"]
        return []
    
    def parse_transaction(self, tx: dict) -> Optional[dict]:
        """Parse transaction into our format."""
        try:
            tx_hash = tx.get("hash", "")
            
            # Skip if already seen
            if tx_hash in self.seen_hashes:
                return None
            
            self.seen_hashes.add(tx_hash)
            
            # Limit cache size
            if len(self.seen_hashes) > self.max_seen_cache:
                self.seen_hashes = set(list(self.seen_hashes)[-5000:])
            
            # Parse hex values
            value = int(tx.get("value", "0x0"), 16)
            gas_price = int(tx.get("gasPrice", tx.get("maxFeePerGas", "0x0")), 16)
            nonce = int(tx.get("nonce", "0x0"), 16)
            
            # Calculate data size
            data = tx.get("input", tx.get("data", "0x"))
            data_size = (len(data) - 2) // 2 if data and len(data) > 2 else 0
            
            return {
                "hash": tx_hash,
                "sender": tx.get("from", ""),
                "recipient": tx.get("to", ""),
                "value": str(value),
                "gas_price": str(gas_price),
                "nonce": nonce,
                "data_size": data_size
            }
        except Exception as e:
            return None
    
    def insert_transaction(self, tx: dict) -> bool:
        """Insert transaction into database."""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO mempool_txs (hash, sender, recipient, value, gas_price, nonce, data_size, first_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hash) DO NOTHING
            """, (
                tx["hash"],
                tx["sender"],
                tx["recipient"],
                tx["value"],
                tx["gas_price"],
                tx["nonce"],
                tx["data_size"],
                datetime.utcnow()
            ))
            self.conn.commit()
            cur.close()
            
            self.tx_count += 1
            record_transaction_received()
            return True
            
        except Exception as e:
            self.conn.rollback()
            return False
    
    def stream_loop(self):
        """Main streaming loop."""
        print("[STREAMER] Starting transaction stream...")
        
        while self.running:
            try:
                # Get pending transactions
                pending_txs = self.get_pending_transactions()
                
                # Also get latest block transactions
                block_txs = self.get_latest_block_transactions()
                
                all_txs = pending_txs + block_txs
                
                new_count = 0
                for tx in all_txs:
                    parsed = self.parse_transaction(tx)
                    if parsed:
                        if self.insert_transaction(parsed):
                            new_count += 1
                
                if new_count > 0:
                    print(f"[STREAMER] Captured {new_count} new transactions (total: {self.tx_count})")
                
                # Rate limit
                time.sleep(2)
                
            except Exception as e:
                print(f"[STREAMER] Error in loop: {e}")
                self.error_count += 1
                time.sleep(5)
                
                # Reconnect DB if needed
                if not self.conn or self.conn.closed:
                    self.connect_db()
    
    def start(self):
        """Start the streamer."""
        if not self.connect_db():
            return False
        
        self.running = True
        self.stream_loop()
        return True
    
    def stop(self):
        """Stop the streamer."""
        self.running = False
        if self.conn:
            self.conn.close()
    
    def get_stats(self) -> dict:
        """Get streamer statistics."""
        return {
            "tx_count": self.tx_count,
            "error_count": self.error_count,
            "last_block": self.last_block,
            "seen_cache_size": len(self.seen_hashes),
            "rpc_url": self.rpc_url[:50] + "..."
        }


def main():
    print("=" * 60)
    print("[STREAMER] Ethereum Live Transaction Streamer")
    print("=" * 60)
    print(f"[STREAMER] RPC: {ETH_RPC_URL}")
    print(f"[STREAMER] DB: {POSTGRES_HOST}/{POSTGRES_DB}")
    print("=" * 60)
    
    streamer = EthereumStreamer()
    
    try:
        streamer.start()
    except KeyboardInterrupt:
        print("\n[STREAMER] Shutting down...")
        streamer.stop()
        print(f"[STREAMER] Final stats: {streamer.get_stats()}")


if __name__ == "__main__":
    main()
