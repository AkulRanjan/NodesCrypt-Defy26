-- Nodescrypt Database Schema
-- Enhanced for EVM-specific features

-- Drop and recreate for clean state (only in dev)
-- DROP TABLE IF EXISTS tx_features CASCADE;
-- DROP TABLE IF EXISTS mempool_txs CASCADE;
-- DROP TABLE IF EXISTS mempool_features CASCADE;
-- DROP TABLE IF EXISTS incidents CASCADE;

-- Raw mempool transactions (CP1)
CREATE TABLE IF NOT EXISTS mempool_txs (
    hash TEXT PRIMARY KEY,
    sender TEXT,
    recipient TEXT,
    value TEXT,
    gas_price TEXT,
    nonce INTEGER,
    data_size INTEGER,
    first_seen TIMESTAMP DEFAULT NOW(),
    
    -- EVM-specific fields
    gas_limit TEXT,
    max_fee_per_gas TEXT,
    max_priority_fee_per_gas TEXT,
    tx_type INTEGER DEFAULT 0,
    access_list TEXT,
    chain_id INTEGER DEFAULT 1,
    
    -- Contract detection
    to_is_contract BOOLEAN DEFAULT FALSE,
    is_erc20 BOOLEAN DEFAULT FALSE,
    is_erc721 BOOLEAN DEFAULT FALSE
);

-- Transaction features (CP2)
CREATE TABLE IF NOT EXISTS tx_features (
    hash TEXT PRIMARY KEY,
    fee_rate DOUBLE PRECISION,
    value DOUBLE PRECISION,
    data_size INTEGER,
    nonce_gap INTEGER,
    sender_tx_count INTEGER,
    sender_avg_fee DOUBLE PRECISION,
    first_seen TIMESTAMP DEFAULT NOW(),
    
    -- EVM-specific features
    to_is_contract BOOLEAN DEFAULT FALSE,
    is_swap BOOLEAN DEFAULT FALSE,
    mev_risk_score DOUBLE PRECISION DEFAULT 0,
    spam_score DOUBLE PRECISION DEFAULT 0,
    
    -- ML predictions
    ml_spam_prediction DOUBLE PRECISION,
    ml_mev_prediction DOUBLE PRECISION,
    
    -- Decision
    decision_action INTEGER,
    decision_timestamp TIMESTAMP
);

-- Mempool snapshots (CP2)
CREATE TABLE IF NOT EXISTS mempool_features (
    snapshot_time TIMESTAMP PRIMARY KEY DEFAULT NOW(),
    tx_count INTEGER,
    avg_fee_rate DOUBLE PRECISION,
    avg_data_size DOUBLE PRECISION,
    congestion_score DOUBLE PRECISION,
    
    -- EVM-specific
    contract_call_ratio DOUBLE PRECISION,
    swap_tx_count INTEGER,
    avg_mev_risk DOUBLE PRECISION
);

-- Security incidents (CP6)
CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    tx_hash TEXT,
    action INTEGER,
    mode TEXT,
    confidence DOUBLE PRECISION,
    explanation_hash TEXT,
    anchor_tx_hash TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_mempool_first_seen ON mempool_txs(first_seen);
CREATE INDEX IF NOT EXISTS idx_mempool_sender ON mempool_txs(sender);
CREATE INDEX IF NOT EXISTS idx_features_spam ON tx_features(spam_score);
CREATE INDEX IF NOT EXISTS idx_features_mev ON tx_features(mev_risk_score);
CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO cp;
