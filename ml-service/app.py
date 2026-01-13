"""
Nodescrypt ML Inference Service
Serves trained XGBoost/GradientBoosting models for spam and MEV detection.

Endpoints:
- /health - Health check
- /predict/spam - Spam detection
- /predict/mev - MEV risk detection
- /predict/full - Full analysis
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import os
from typing import Optional, Dict, Any

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
ML_DIR = os.path.join(BASE_DIR, "ml")

app = FastAPI(title="Nodescrypt ML Inference Service", version="2.0")

# Model loading with fallback
spam_model = None
mev_model = None
models_loaded = False

def load_models():
    """Load trained models with fallback."""
    global spam_model, mev_model, models_loaded
    
    # Try new models first (from models/ directory)
    spam_paths = [
        os.path.join(MODELS_DIR, "spam_model.joblib"),
        os.path.join(ML_DIR, "spam_model.pkl"),
    ]
    
    mev_paths = [
        os.path.join(MODELS_DIR, "mev_model.joblib"),
        os.path.join(ML_DIR, "mempool_model.pkl"),
    ]
    
    for path in spam_paths:
        if os.path.exists(path):
            try:
                spam_model = joblib.load(path)
                print(f"[ML-SERVICE] Loaded spam model from {path}")
                break
            except Exception as e:
                print(f"[ML-SERVICE] Failed to load {path}: {e}")
    
    for path in mev_paths:
        if os.path.exists(path):
            try:
                mev_model = joblib.load(path)
                print(f"[ML-SERVICE] Loaded MEV model from {path}")
                break
            except Exception as e:
                print(f"[ML-SERVICE] Failed to load {path}: {e}")
    
    models_loaded = (spam_model is not None)
    return models_loaded


# Load models on startup
load_models()


class TxFeatures(BaseModel):
    """Transaction features for spam detection."""
    fee_rate: float = 0.0
    value: float = 0.0
    data_size: int = 0
    nonce_gap: int = 0
    sender_tx_count: int = 1
    sender_avg_fee: float = 0.0


class MEVFeatures(BaseModel):
    """Transaction features for MEV detection."""
    fee_rate: float = 0.0
    value: float = 0.0
    data_size: int = 0
    to_is_contract: int = 0
    is_swap: int = 0
    mev_risk_score: float = 0.0


class FullFeatures(BaseModel):
    """Full feature set for comprehensive analysis."""
    fee_rate: float = 0.0
    value: float = 0.0
    data_size: int = 0
    nonce_gap: int = 0
    sender_tx_count: int = 1
    sender_avg_fee: float = 0.0
    to_is_contract: int = 0
    is_swap: int = 0
    mev_risk_score: float = 0.0


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok" if models_loaded else "degraded",
        "models_loaded": models_loaded,
        "spam_model": spam_model is not None,
        "mev_model": mev_model is not None,
        "version": "2.0"
    }


@app.post("/predict/spam")
def predict_spam(f: TxFeatures):
    """Predict spam score for a transaction."""
    if spam_model is None:
        # Fallback to heuristic
        score = 0.0
        if f.fee_rate < 1: score += 0.3
        if f.sender_tx_count > 10: score += 0.3
        if f.nonce_gap > 5: score += 0.4
        return {"spam_score": min(score, 1.0), "source": "heuristic"}
    
    try:
        # Features: fee_rate, value, data_size, nonce_gap, sender_tx_count, sender_avg_fee
        X = np.array([[f.fee_rate, f.value, f.data_size, f.nonce_gap, 
                       f.sender_tx_count, f.sender_avg_fee]])
        
        proba = spam_model.predict_proba(X)
        score = float(proba[0][1]) if proba.shape[1] > 1 else float(proba[0][0])
        
        return {"spam_score": score, "source": "model"}
    except Exception as e:
        return {"spam_score": 0.0, "source": "error", "error": str(e)}


@app.post("/predict/mev")
def predict_mev(f: MEVFeatures):
    """Predict MEV risk for a transaction."""
    if mev_model is None:
        # Fallback to heuristic
        score = 0.0
        if f.is_swap: score += 0.4
        if f.to_is_contract: score += 0.2
        if f.value > 1: score += 0.2
        return {"mev_score": min(score, 1.0), "source": "heuristic"}
    
    try:
        # Features: fee_rate, value, data_size, to_is_contract, is_swap, mev_risk_score
        X = np.array([[f.fee_rate, f.value, f.data_size, f.to_is_contract,
                       f.is_swap, f.mev_risk_score]])
        
        proba = mev_model.predict_proba(X)
        score = float(proba[0][1]) if proba.shape[1] > 1 else float(proba[0][0])
        
        return {"mev_score": score, "source": "model"}
    except Exception as e:
        return {"mev_score": 0.0, "source": "error", "error": str(e)}


@app.post("/predict/full")
def predict_full(f: FullFeatures):
    """Full analysis with spam and MEV predictions."""
    spam_result = predict_spam(TxFeatures(
        fee_rate=f.fee_rate,
        value=f.value,
        data_size=f.data_size,
        nonce_gap=f.nonce_gap,
        sender_tx_count=f.sender_tx_count,
        sender_avg_fee=f.sender_avg_fee
    ))
    
    mev_result = predict_mev(MEVFeatures(
        fee_rate=f.fee_rate,
        value=f.value,
        data_size=f.data_size,
        to_is_contract=f.to_is_contract,
        is_swap=f.is_swap,
        mev_risk_score=f.mev_risk_score
    ))
    
    # Determine action recommendation
    spam_score = spam_result["spam_score"]
    mev_score = mev_result["mev_score"]
    
    if spam_score > 0.9:
        action = "DROP"
    elif spam_score > 0.7 or mev_score > 0.8:
        action = "DELAY"
    elif mev_score > 0.6:
        action = "TAG"
    else:
        action = "PASS"
    
    return {
        "spam_score": spam_score,
        "mev_score": mev_score,
        "action": action,
        "risk_level": "HIGH" if spam_score > 0.7 or mev_score > 0.7 else "MEDIUM" if spam_score > 0.3 or mev_score > 0.3 else "LOW"
    }


@app.post("/reload")
def reload_models():
    """Reload models from disk."""
    success = load_models()
    return {"success": success, "models_loaded": models_loaded}


# Backwards compatibility endpoints
class MempoolFeatures(BaseModel):
    tx_count: int = 0
    avg_fee_rate: float = 0.0
    avg_data_size: float = 0.0


@app.post("/predict/congestion")
def predict_congestion(m: MempoolFeatures):
    """Legacy congestion prediction (simple heuristic)."""
    score = min(m.tx_count / 10000, 1.0) * 0.5 + min(m.avg_fee_rate / 100, 1.0) * 0.5
    return {"congestion_score": float(score)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
