# Checkpoint Security Middleware — Manual Setup Guide

> **Step-by-Step Instructions to Run the Entire System from Scratch**

---

## Prerequisites

Before starting, ensure you have:

- [ ] **Docker Desktop** installed and running
- [ ] **Python 3.10+** installed
- [ ] **Node.js 18+** installed
- [ ] **Git** installed

---

## Quick Start (TL;DR)

```powershell
# 1. Start PostgreSQL
docker-compose -f infra/docker-compose.yml up -d

# 2. Install Python dependencies
pip install psycopg2-binary pandas numpy xgboost scikit-learn joblib fastapi uvicorn gymnasium stable-baselines3 requests

# 3. Start feature extractor (Terminal 1)
python features/extract_features.py

# 4. Start ML service (Terminal 2)
cd ml-service && uvicorn app:app --host 127.0.0.1 --port 8002

# 5. Run the full system (Terminal 3)
python mitigation/control_loop.py
```

---

## Detailed Step-by-Step Guide

### Step 1: Clone and Enter Project

```powershell
cd C:\Users\asus\eth_india
cd blockchain-cp-checkpoint
```

---

### Step 2: Start Docker Desktop

1. Open Docker Desktop application
2. Wait until it shows "Docker Desktop is running"
3. Verify with:

```powershell
docker --version
# Expected: Docker version 24.x.x
```

---

### Step 3: Start PostgreSQL (CP1 Infrastructure)

```powershell
# Start PostgreSQL container
docker-compose -f infra/docker-compose.yml up -d

# Wait 5 seconds for startup
Start-Sleep -Seconds 5

# Verify it's running
docker ps
# Expected: cp_postgres container running
```

**Verify database connection:**
```powershell
docker exec -it cp_postgres psql -U cp -d checkpoint -c "\dt"
# Expected: List of tables (mempool_txs, tx_features, mempool_features)
```

---

### Step 4: Create Database Tables (if not exists)

```powershell
# Create CP1 table
docker exec -it cp_postgres psql -U cp -d checkpoint -c "
CREATE TABLE IF NOT EXISTS mempool_txs (
    hash TEXT PRIMARY KEY,
    sender TEXT,
    recipient TEXT,
    value TEXT,
    gas_price TEXT,
    nonce INT,
    data_size INT,
    first_seen TIMESTAMP DEFAULT NOW()
);"

# Create CP2 tables
docker exec -it cp_postgres psql -U cp -d checkpoint -c "
CREATE TABLE IF NOT EXISTS tx_features (
    hash TEXT PRIMARY KEY,
    fee_rate DOUBLE PRECISION,
    value DOUBLE PRECISION,
    data_size INT,
    nonce_gap INT,
    sender_tx_count INT,
    sender_avg_fee DOUBLE PRECISION,
    first_seen TIMESTAMP
);"

docker exec -it cp_postgres psql -U cp -d checkpoint -c "
CREATE TABLE IF NOT EXISTS mempool_features (
    snapshot_time TIMESTAMP PRIMARY KEY,
    tx_count INT,
    avg_fee_rate DOUBLE PRECISION,
    avg_data_size DOUBLE PRECISION,
    congestion_score DOUBLE PRECISION
);"
```

---

### Step 5: Install Python Dependencies

```powershell
# Install all required packages
pip install psycopg2-binary pandas numpy xgboost scikit-learn joblib fastapi uvicorn gymnasium stable-baselines3 requests

# Verify installation
python -c "import psycopg2, pandas, xgboost, fastapi, stable_baselines3; print('All packages OK')"
```

---

### Step 6: Seed Sample Data (if mempool is empty)

```powershell
# Insert sample transactions
docker exec -it cp_postgres psql -U cp -d checkpoint -c "
INSERT INTO mempool_txs (hash, sender, recipient, value, gas_price, nonce, data_size)
VALUES 
    ('0xabc123', '0xuser1', '0xmerchant1', '1000000000', '50000000000', 1, 100),
    ('0xdef456', '0xuser2', '0xmerchant2', '2000000000', '60000000000', 2, 150),
    ('0xghi789', '0xuser3', '0xmerchant3', '500000000', '40000000000', 1, 80),
    ('0xjkl012', '0xspammer', '0xvictim', '100', '1000000', 1, 500),
    ('0xmno345', '0xspammer', '0xvictim2', '200', '2000000', 2, 600)
ON CONFLICT DO NOTHING;
"

# Verify data
docker exec -it cp_postgres psql -U cp -d checkpoint -c "SELECT COUNT(*) FROM mempool_txs;"
```

---

### Step 7: Start CP2 Feature Extractor

**Open Terminal 1:**

```powershell
cd C:\Users\asus\eth_india\blockchain-cp-checkpoint

# Run feature extractor (runs continuously)
python features/extract_features.py
```

**Expected output:**
```
[CP2] Features updated
[CP2] Features updated
...
```

**Leave this terminal running!**

---

### Step 8: Train ML Models (CP3) — One Time Only

**Open Terminal 2:**

```powershell
cd C:\Users\asus\eth_india\blockchain-cp-checkpoint

# Prepare training data
python ml/prepare_data.py
# Expected: [CP3] Training data prepared: (N, columns)

# Train spam model
python ml/train_spam_model.py
# Expected: Classification report + [CP3] Spam model saved

# Train mempool model
python ml/train_mempool_model.py
# Expected: [CP3] Mempool model trained
```

**Verify models exist:**
```powershell
dir ml\*.pkl
# Expected: spam_model.pkl, mempool_model.pkl
```

---

### Step 9: Start ML Service (CP3)

**In Terminal 2:**

```powershell
cd C:\Users\asus\eth_india\blockchain-cp-checkpoint\ml-service

# Start FastAPI ML service
uvicorn app:app --host 127.0.0.1 --port 8002
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8002
INFO:     Application startup complete.
```

**Leave this terminal running!**

**Verify ML service:**
```powershell
# In a new terminal
Invoke-RestMethod -Uri http://127.0.0.1:8002/health
# Expected: status: ok, models_loaded: True
```

---

### Step 10: Train RL Policy (CP4) — One Time Only

**Open Terminal 3:**

```powershell
cd C:\Users\asus\eth_india\blockchain-cp-checkpoint\rl

# Train RL policy (takes ~30 seconds)
python train.py
```

**Expected output:**
```
| time/                   |              |
|    fps                  | 1137         |
|    total_timesteps      | 30720        |
[CP4] RL policy trained
```

**Verify policy exists:**
```powershell
dir rl\checkpoint_rl_policy.zip
# Expected: checkpoint_rl_policy.zip
```

---

### Step 11: Run Full System (CP4-CP7)

**In Terminal 3:**

```powershell
cd C:\Users\asus\eth_india\blockchain-cp-checkpoint

# Run the full control loop
python mitigation/control_loop.py
```

**Expected output:**
```
============================================================
[CP1-CP7] FULL AUTONOMOUS SECURITY LOOP
============================================================

[CYCLE 1]
[STATE] tx=5, spam=0.25, congestion=4316820075
[CP4] Decision: 3 (DEFENSIVE_MODE)
[CP5] ⚠️ DEFENSIVE MODE ENABLED
[CP6] 🔐 Incident: 61e8a7797dcf... Risk: 100
[CP7] 🚨 DRIFT ALERTS: [CRITICAL] CRITICAL_RISK
[CP7] 🔧 HEALING: ['MAX_DEFENSE']
...
```

---

### Step 12: Run Demo (Optional)

```powershell
cd C:\Users\asus\eth_india\blockchain-cp-checkpoint

# Run the ETHIndia demo
python demo/run_demo.py
```

---

## Terminal Summary

| Terminal | Command | Purpose |
|----------|---------|---------|
| 1 | `python features/extract_features.py` | CP2 Feature Extraction |
| 2 | `uvicorn app:app --host 127.0.0.1 --port 8002` | CP3 ML Service |
| 3 | `python mitigation/control_loop.py` | CP4-CP7 Full Loop |

---

## Verify Everything is Working

### Check Database
```powershell
docker exec -it cp_postgres psql -U cp -d checkpoint -c "
SELECT 
    (SELECT COUNT(*) FROM mempool_txs) as raw_txs,
    (SELECT COUNT(*) FROM tx_features) as features,
    (SELECT COUNT(*) FROM mempool_features) as snapshots;
"
```

### Check ML Service
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8002/health
```

### Check Control Loop Output
Look for these in Terminal 3:
- `[CP4] Decision:` — RL is working
- `[CP5] ⚠️ DEFENSIVE MODE` — Mitigation working
- `[CP6] 🔐 Incident:` — INCO logging working
- `[CP7] 🔧 HEALING:` — Self-healing working

---

## Troubleshooting

### PostgreSQL Won't Start
```powershell
# Check if Docker is running
docker ps

# Restart PostgreSQL
docker-compose -f infra/docker-compose.yml down
docker-compose -f infra/docker-compose.yml up -d
```

### Python Import Errors
```powershell
# Reinstall all packages
pip install --force-reinstall psycopg2-binary pandas numpy xgboost scikit-learn
```

### ML Service Port Conflict
```powershell
# Use a different port
uvicorn app:app --host 127.0.0.1 --port 8003

# Update ML_SERVICE_URL in decision_engine.py
```

### No Data in Features
```powershell
# Check if mempool has data
docker exec -it cp_postgres psql -U cp -d checkpoint -c "SELECT COUNT(*) FROM mempool_txs;"

# If 0, insert sample data (Step 6)
```

---

## Stopping the System

```powershell
# Stop Python processes with Ctrl+C in each terminal

# Stop PostgreSQL
docker-compose -f infra/docker-compose.yml down
```

---

## File Locations Quick Reference

| Component | Path |
|-----------|------|
| Feature Extractor | `features/extract_features.py` |
| ML Training | `ml/train_*.py` |
| ML Models | `ml/*.pkl` |
| ML Service | `ml-service/app.py` |
| RL Environment | `rl/env.py` |
| RL Policy | `rl/checkpoint_rl_policy.zip` |
| Control Loop | `mitigation/control_loop.py` |
| Demo | `demo/run_demo.py` |

---

**You're all set! 🚀**
