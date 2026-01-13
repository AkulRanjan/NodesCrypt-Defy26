import psycopg2
import pandas as pd

conn = psycopg2.connect(
    host="localhost",
    database="checkpoint",
    user="cp",
    password="cp"
)

# Load features
df = pd.read_sql("SELECT * FROM tx_features", conn)

# ---- LABELING (temporary for hackathon) ----
# Heuristic: low fee + high sender_tx_count = spam
df["label"] = (
    (df["fee_rate"] < df["fee_rate"].quantile(0.2)) &
    (df["sender_tx_count"] > 3)
).astype(int)

df.to_csv("ml/tx_train.csv", index=False)
print("[CP3] Training data prepared:", df.shape)
