# Checkpoint Security Middleware — Governance Model

## Overview

Checkpoint is a **sidecar security middleware** that runs alongside EVM validator nodes. It enforces local security policies without modifying blockchain consensus.

## Governance Principles

1. **Validators opt-in** — No forced participation
2. **Policies are configurable** — Thresholds can be tuned
3. **Actions are auditable** — All decisions logged via INCO
4. **Sensitive data is confidential** — Zero data leakage

## Actor Control Matrix

| Actor | Control |
|-------|---------|
| **Validator** | Enable/disable checkpoint, choose mitigation level |
| **Governance** | Update thresholds, approve model updates |
| **System (RL)** | Autonomous real-time actions within policy bounds |
| **Auditors** | View INCO logs (permissioned access only) |

## Configurable Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `min_fee_threshold` | 0 gwei | 0-1000 | Minimum fee to admit transactions |
| `spam_score_threshold` | 0.5 | 0-1 | Score above which tx is flagged |
| `defensive_mode_auto` | true | bool | Allow RL to activate defensive mode |
| `audit_to_inco` | true | bool | Log incidents to INCO |

## Decision Audit Trail

Every RL decision is:
- **Hashed** — Deterministic SHA256 incident ID
- **Timestamped** — UTC timestamp
- **Logged** — To INCO confidential ledger
- **Recoverable** — Can be verified by auditors

## INCO Integration

**What we store (confidentially):**
- Decision hash
- Action taken (0-3)
- Risk score (0-100)
- Timestamp

**What we NEVER store:**
- IP addresses
- Wallet balances
- Raw transaction data
- Mempool contents

## Deployment Model

```
┌─────────────────────────────────────┐
│         Shardeum Validator          │
│  ┌─────────────────────────────┐   │
│  │   Checkpoint Sidecar        │   │
│  │  ├─ CP1 Ingestion           │   │
│  │  ├─ CP2 Features            │   │
│  │  ├─ CP3 ML Detection        │   │
│  │  ├─ CP4 RL Decision         │   │
│  │  ├─ CP5 Mitigation          │   │
│  │  ├─ CP6 INCO Audit          │   │
│  │  └─ CP7 Self-Healing        │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Key phrase for judges:**
> "Governance can audit decisions without seeing sensitive transaction data."
