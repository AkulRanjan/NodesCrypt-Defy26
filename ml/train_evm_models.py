"""
Nodescrypt ML Training Pipeline
Train XGBoost spam/MEV classifiers on EVM transaction data

Usage:
    python train_evm_models.py --data-source db  # From PostgreSQL
    python train_evm_models.py --data-source csv --file data.csv
"""
import os
import sys
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve
import joblib

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
XGB_AVAILABLE = False  # Force sklearn for reliability

try:
    import psycopg2
    DB_AVAILABLE = True
except:
    DB_AVAILABLE = False


def load_data_from_db():
    """Load training data from PostgreSQL."""
    if not DB_AVAILABLE:
        raise Exception("psycopg2 not installed")
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "checkpoint"),
        user=os.getenv("POSTGRES_USER", "cp"),
        password=os.getenv("POSTGRES_PASSWORD", "cp")
    )
    
    query = """
        SELECT 
            fee_rate,
            value,
            data_size,
            nonce_gap,
            sender_tx_count,
            sender_avg_fee,
            COALESCE(to_is_contract::int, 0) as to_is_contract,
            COALESCE(is_swap::int, 0) as is_swap,
            COALESCE(mev_risk_score, 0) as mev_risk_score,
            COALESCE(spam_score, 0) as spam_score
        FROM tx_features
        WHERE fee_rate IS NOT NULL
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"[TRAIN] Loaded {len(df)} rows from database")
    return df


def load_data_from_csv(filepath):
    """Load training data from CSV."""
    df = pd.read_csv(filepath)
    print(f"[TRAIN] Loaded {len(df)} rows from {filepath}")
    return df


def create_labels(df):
    """Create training labels using heuristics."""
    # Spam label: low fee + high sender activity
    df['is_spam'] = (
        (df['fee_rate'] < 1) |  # Very low fee
        (df['sender_tx_count'] > 10) |  # High activity
        (df['nonce_gap'] > 5)  # Nonce flooding
    ).astype(int)
    
    # MEV label: swap + high value + contract interaction
    df['is_mev_target'] = (
        (df['is_swap'] == 1) |
        (df['mev_risk_score'] > 0.5) |
        ((df['to_is_contract'] == 1) & (df['value'] > 0.1))
    ).astype(int)
    
    print(f"[TRAIN] Labels created: spam={df['is_spam'].sum()}, mev={df['is_mev_target'].sum()}")
    return df


def train_spam_model(df):
    """Train spam detection model."""
    print("\n[TRAIN] Training Spam Detection Model...")
    
    features = ['fee_rate', 'value', 'data_size', 'nonce_gap', 'sender_tx_count', 'sender_avg_fee']
    X = df[features].fillna(0)
    y = df['is_spam']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    if XGB_AVAILABLE:
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            random_state=42,
            objective='binary:logistic'
        )
    else:
        model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            random_state=42
        )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    print("\n[TRAIN] Spam Model Performance:")
    print(classification_report(y_test, y_pred))
    
    if len(np.unique(y_test)) > 1:
        auc = roc_auc_score(y_test, y_proba)
        print(f"[TRAIN] ROC AUC: {auc:.4f}")
    
    # Feature importance
    if XGB_AVAILABLE:
        importance = dict(zip(features, model.feature_importances_))
        print("\n[TRAIN] Feature Importance:")
        for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
            print(f"  {feat}: {imp:.4f}")
    
    return model, features


def train_mev_model(df):
    """Train MEV risk detection model."""
    print("\n[TRAIN] Training MEV Risk Model...")
    
    features = ['fee_rate', 'value', 'data_size', 'to_is_contract', 'is_swap', 'mev_risk_score']
    X = df[features].fillna(0)
    y = df['is_mev_target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    if XGB_AVAILABLE:
        model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            random_state=42,
            objective='binary:logistic'
        )
    else:
        model = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            random_state=42
        )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    
    print("\n[TRAIN] MEV Model Performance:")
    print(classification_report(y_test, y_pred))
    
    return model, features


def save_models(spam_model, mev_model, output_dir="models"):
    """Save trained models."""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    spam_path = os.path.join(output_dir, f"spam_model_{timestamp}.joblib")
    mev_path = os.path.join(output_dir, f"mev_model_{timestamp}.joblib")
    
    joblib.dump(spam_model, spam_path)
    joblib.dump(mev_model, mev_path)
    
    # Also save as latest
    joblib.dump(spam_model, os.path.join(output_dir, "spam_model.joblib"))
    joblib.dump(mev_model, os.path.join(output_dir, "mev_model.joblib"))
    
    print(f"\n[TRAIN] Models saved to {output_dir}/")
    print(f"  - {spam_path}")
    print(f"  - {mev_path}")


def main():
    parser = argparse.ArgumentParser(description="Train Nodescrypt ML models")
    parser.add_argument("--data-source", choices=["db", "csv"], default="db")
    parser.add_argument("--file", help="CSV file path (if data-source=csv)")
    parser.add_argument("--output", default="models", help="Output directory")
    args = parser.parse_args()
    
    print("=" * 60)
    print("[NODESCRYPT] ML Training Pipeline")
    print("=" * 60)
    
    # Load data
    if args.data_source == "db":
        df = load_data_from_db()
    else:
        if not args.file:
            print("Error: --file required for csv data source")
            return
        df = load_data_from_csv(args.file)
    
    if len(df) < 100:
        print("[TRAIN] Warning: Very small dataset, results may be unreliable")
    
    # Create labels
    df = create_labels(df)
    
    # Train models
    spam_model, spam_features = train_spam_model(df)
    mev_model, mev_features = train_mev_model(df)
    
    # Save
    save_models(spam_model, mev_model, args.output)
    
    print("\n[TRAIN] Training complete!")


if __name__ == "__main__":
    main()
