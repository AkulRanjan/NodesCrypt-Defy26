import psycopg2
import psycopg2.extensions
import numpy as np
import pandas as pd
import time
from datetime import datetime

# Register numpy type adapters for psycopg2
psycopg2.extensions.register_adapter(np.int64, lambda x: psycopg2.extensions.AsIs(int(x)))
psycopg2.extensions.register_adapter(np.float64, lambda x: psycopg2.extensions.AsIs(float(x)))

conn = psycopg2.connect(
    host="localhost",
    database="checkpoint",
    user="cp",
    password="cp"
)

def extract_tx_features():
    txs = pd.read_sql("""
        SELECT * FROM mempool_txs
        WHERE hash NOT IN (SELECT hash FROM tx_features)
    """, conn)

    if txs.empty:
        return

    features = []

    for _, tx in txs.iterrows():
        gas_price = float(tx["gas_price"] or 0)
        data_size = int(tx["data_size"]) if tx["data_size"] else 1
        fee_rate = gas_price / data_size

        sender = tx["sender"]

        sender_stats = pd.read_sql(f"""
            SELECT COUNT(*) as cnt, AVG(gas_price::FLOAT / GREATEST(data_size,1)) as avg_fee
            FROM mempool_txs
            WHERE sender = '{sender}'
        """, conn)

        last_nonce = pd.read_sql(f"""
            SELECT MAX(nonce) as max_nonce
            FROM mempool_txs
            WHERE sender = '{sender}'
        """, conn)["max_nonce"].iloc[0]
        
        if pd.isna(last_nonce):
            last_nonce = int(tx["nonce"])
        else:
            last_nonce = int(last_nonce)

        nonce_gap = int(tx["nonce"]) - last_nonce

        # Convert first_seen to Python datetime
        first_seen = tx["first_seen"]
        if hasattr(first_seen, 'to_pydatetime'):
            first_seen = first_seen.to_pydatetime()

        avg_fee = sender_stats["avg_fee"].iloc[0]
        if pd.isna(avg_fee):
            avg_fee = fee_rate

        features.append((
            str(tx["hash"]),
            float(fee_rate),
            float(tx["value"] or 0),
            int(data_size),
            int(nonce_gap),
            int(sender_stats["cnt"].iloc[0]),
            float(avg_fee),
            first_seen
        ))

    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO tx_features
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """, features)
    conn.commit()
    cur.close()

def extract_mempool_snapshot():
    df = pd.read_sql("SELECT * FROM tx_features", conn)
    if df.empty:
        return

    snapshot = (
        datetime.utcnow(),
        int(len(df)),
        float(df["fee_rate"].mean()),
        float(df["data_size"].mean()),
        float(len(df) * df["fee_rate"].mean())
    )

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mempool_features
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """, snapshot)
    conn.commit()
    cur.close()

if __name__ == "__main__":
    while True:
        extract_tx_features()
        extract_mempool_snapshot()
        print("[CP2] Features updated")
        time.sleep(5)
