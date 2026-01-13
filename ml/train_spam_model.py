import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier
import joblib

df = pd.read_csv("ml/tx_train.csv")

X = df[[
    "fee_rate",
    "data_size",
    "nonce_gap",
    "sender_tx_count",
    "sender_avg_fee"
]]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = XGBClassifier(
    n_estimators=50,
    max_depth=4,
    learning_rate=0.1,
    eval_metric="logloss"
)

model.fit(X_train, y_train)

print(classification_report(y_test, model.predict(X_test)))

joblib.dump(model, "ml/spam_model.pkl")
print("[CP3] Spam model saved")
