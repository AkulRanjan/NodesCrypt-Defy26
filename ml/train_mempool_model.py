import psycopg2
import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

conn = psycopg2.connect(
    host="localhost",
    database="checkpoint",
    user="cp",
    password="cp"
)

df = pd.read_sql("SELECT * FROM mempool_features", conn)

X = df[["tx_count", "avg_fee_rate", "avg_data_size"]]
y = df["congestion_score"]

model = LinearRegression()
model.fit(X, y)

joblib.dump(model, "ml/mempool_model.pkl")
print("[CP3] Mempool model trained")
