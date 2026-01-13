# Checkpoint Security Middleware

> **Privacy-preserving AI security middleware for EVM blockchains that autonomously detects, mitigates, and audits mempool-level attacks in real time.**

[![ETHIndia 2026](https://img.shields.io/badge/ETHIndia-2026-blue)](https://ethindia.co)
[![Shardeum](https://img.shields.io/badge/Shardeum-Native-green)](https://shardeum.org)
[![INCO](https://img.shields.io/badge/INCO-Confidential-purple)](https://inco.network)

## 🎯 What is Checkpoint?

Checkpoint is a **sidecar security middleware** that runs alongside EVM validators to:

- **Detect** spam, DoS, and fee manipulation attacks using ML
- **Decide** optimal mitigation actions using Reinforcement Learning
- **Mitigate** attacks with local node policies (no consensus changes)
- **Audit** all decisions confidentially via INCO

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────┐
│                Shardeum Validator                  │
│  ┌─────────────────────────────────────────────┐  │
│  │         Checkpoint Sidecar                   │  │
│  │                                              │  │
│  │  CP1 → CP2 → CP3 → CP4 → CP5 → CP6 → CP7    │  │
│  │  Data  Features ML   RL  Action INCO Monitor │  │
│  └─────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# Clone and enter
git clone <repo>
cd blockchain-cp-checkpoint

# Start all services
docker-compose up -d

# Run the security loop
python mitigation/control_loop.py
```

## 📦 Checkpoints

| CP | Component | Description |
|----|-----------|-------------|
| 1 | Ingestion | Real-time mempool data capture |
| 2 | Features | ML-ready feature engineering |
| 3 | Detection | XGBoost spam/anomaly detection |
| 4 | Decision | PPO reinforcement learning policy |
| 5 | Mitigation | Node-level security actions |
| 6 | Audit | INCO confidential logging |
| 7 | Healing | Self-monitoring and adaptation |
| 8 | Deploy | Production-ready packaging |

## 🎬 Demo (ETHIndia)

```bash
# 1. Start the system
docker-compose up -d

# 2. Run attack simulation
python demo/attack_sim.py

# 3. Watch the response
python mitigation/control_loop.py
```

**What happens:**
1. Normal traffic → NORMAL mode
2. Spam flood → ML detects, RL activates DEFENSIVE_MODE
3. Fee threshold raised → Spam filtered
4. Incident logged → INCO audit
5. System self-heals → Stability restored

## 🔐 INCO Integration

**What we log (confidentially):**
- Decision hash
- Action taken
- Risk score
- Timestamp

**What we NEVER log:**
- IPs, wallet balances, raw tx data

> "Privacy-preserving auditability"

## 🏛️ Governance

See [GOVERNANCE.md](./GOVERNANCE.md) for:
- Actor control matrix
- Configurable parameters
- Deployment model

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| Detection latency | <100ms |
| RL decision time | <10ms |
| Audit log time | <1s (INCO) |

## 🛣️ Roadmap

- [x] CP1-CP8: Core system
- [ ] CP9: Multi-validator coordination
- [ ] CP10: MEV-aware defenses
- [ ] CP11: Shared threat intel
- [ ] CP12: SaaS for EVM chains

## 📜 License

MIT

---

**Built with ❤️ at ETHIndia 2026**
