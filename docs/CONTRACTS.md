# NodesCrypt Smart Contracts

> **Production-grade, RBAC-controlled, event-first smart contracts for on-chain security auditing**

## Contract Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ContractRegistry                                │
│                 (Central address lookup)                            │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┬──────────────────┐
    │                     │                     │                  │
    ▼                     ▼                     ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│SecurityAudit│   │MerkleBatch  │   │PolicyRegistry│  │ AddressBook │
│(Incidents)  │   │Anchor       │   │(Policies)    │  │(Watchlist)  │
└─────────────┘   └─────────────┘   └─────────────┘  └─────────────┘
                          │
                          ▼
                ┌─────────────────┐
                │   Governance    │
                │ (Voting/Rules)  │
                └─────────────────┘
```

---

## Contracts

### 1. ContractRegistry.sol

**Purpose**: Central index for all NodesCrypt contract addresses.

**Key Functions**:
| Function | Role Required | Description |
|----------|---------------|-------------|
| `setContract(name, addr)` | ADMIN_ROLE | Register/update contract address |
| `getContract(name)` | View | Get address by name |
| `getContractByHash(nameHash)` | View | Gas-efficient lookup |
| `removeContract(name)` | ADMIN_ROLE | Soft delete (set to zero) |

**Events**:
- `ContractUpdated(nameHash, name, addr, version, timestamp)`
- `ContractRemoved(nameHash, name, timestamp)`

---

### 2. SecurityAudit.sol

**Purpose**: Immutable incident anchor for security decisions.

**What Gets Logged**:
- `incidentId`: SHA256 hash of decision payload
- `action`: 0=PASS, 1=DELAY, 2=DROP, 3=ESCALATE
- `modelId`: ML model version identifier
- `riskScore`: 0-100 scale

**What's NEVER Logged**:
- ❌ IP addresses
- ❌ Wallet balances
- ❌ Raw transaction data
- ❌ ML features

**Key Functions**:
| Function | Role Required | Description |
|----------|---------------|-------------|
| `logIncident(id, action, modelId, riskScore)` | PUBLISHER_ROLE | Log single incident |
| `logIncidentBatch(ids[], actions[], modelId, scores[])` | PUBLISHER_ROLE | Batch log (max 50) |
| `registerModel(modelId, version)` | PUBLISHER_ROLE | Register model version |
| `incidentExists(id)` | View | Check if logged |

**Events**:
- `IncidentLogged(incidentId, action, modelId, riskScore, timestamp, reporter)`
- `ModelRegistered(modelId, version, timestamp)`

**Gas Cost**: ~50,000 gas per incident (single), ~35,000 per incident (batched)

---

### 3. MerkleBatchAnchor.sol

**Purpose**: Gas-optimized batch anchoring using Merkle trees.

**Flow**:
1. Collect N incident hashes off-chain
2. Build Merkle tree, compute root
3. Call `anchorBatch(root, modelId, batchSize)` - single tx
4. Store proofs off-chain for verification

**Gas Savings**: ~21,000 gas per anchor vs ~50,000 per individual log

**Key Functions**:
| Function | Role Required | Description |
|----------|---------------|-------------|
| `anchorBatch(root, modelId, size)` | PUBLISHER_ROLE | Anchor Merkle root |
| `verifyIncident(root, leaf, proof)` | View | Verify with Merkle proof |
| `batchExists(root)` | View | Check if batch exists |

**Events**:
- `BatchAnchored(root, modelId, batchSize, timestamp, reporter)`
- `BatchVerified(root, leaf, verifier)`

---

### 4. PolicyRegistry.sol

**Purpose**: Registry for security policies with validator assignments.

**Design**: Store only hashes on-chain, actual policies encrypted in INCO.

**Key Functions**:
| Function | Role Required | Description |
|----------|---------------|-------------|
| `createPolicy(id, contentHash, keyId, version)` | POLICY_ADMIN | Create policy |
| `updatePolicy(id, newHash, version)` | POLICY_ADMIN | Update policy |
| `setPolicyStatus(id, status)` | POLICY_ADMIN | Activate/pause |
| `assignPolicy(validator, policyId)` | POLICY_ADMIN | Assign to validator |
| `getEffectivePolicy(validator)` | View | Get validator's policy |

**Policy Status**: INACTIVE, ACTIVE, PAUSED, DEPRECATED

**Events**:
- `PolicyCreated(policyId, contentHash, version, timestamp)`
- `PolicyAssigned(validator, policyId, timestamp)`
- `GlobalPolicySet(policyId, timestamp)`

---

### 5. Governance.sol

**Purpose**: Proposal and voting system for rule changes.

**Features**:
- Multi-signer approval
- Timelock for execution
- Support for rule changes, upgrades, emergencies
- Integrates with Gnosis Safe for production

**Proposal Types**: RULE_CHANGE, PARAMETER_UPDATE, CONTRACT_UPGRADE, ROLE_GRANT, EMERGENCY

**Key Functions**:
| Function | Role Required | Description |
|----------|---------------|-------------|
| `createProposal(type, hash, desc)` | PROPOSER_ROLE | Create proposal |
| `vote(proposalId, approve)` | VOTER_ROLE | Cast vote |
| `executeProposal(proposalId)` | EXECUTOR_ROLE | Execute approved proposal |
| `emergencyAction(hash)` | DEFAULT_ADMIN | Bypass governance |

**Events**:
- `ProposalCreated(proposalId, type, hash, proposer, expiresAt)`
- `ProposalVoted(proposalId, voter, approved)`
- `ProposalExecuted(proposalId, timestamp)`
- `RuleApproved(ruleHash, proposalId, timestamp)`

---

### 6. AddressBook.sol

**Purpose**: Registry of monitored high-risk addresses.

**Use Case**: Sidecars read this to apply higher scrutiny to DEX pools, bridges, etc.

**Risk Levels**: UNKNOWN, LOW, MEDIUM, HIGH, CRITICAL

**Key Functions**:
| Function | Role Required | Description |
|----------|---------------|-------------|
| `addAddress(addr, risk, category, label)` | CURATOR_ROLE | Add to watchlist |
| `updateRiskLevel(addr, newLevel)` | CURATOR_ROLE | Update risk |
| `addAddressBatch(addrs[], levels[], category)` | CURATOR_ROLE | Batch add |
| `isWatched(addr)` | View | Check if monitored |
| `getRiskLevel(addr)` | View | Get risk level |

**Events**:
- `AddressWatched(addr, riskLevel, category, labelHash, timestamp)`
- `AddressUpdated(addr, riskLevel, active, timestamp)`

---

## RBAC Roles

| Role | Used In | Purpose |
|------|---------|---------|
| `DEFAULT_ADMIN_ROLE` | All | Grant/revoke roles, emergency actions |
| `ADMIN_ROLE` | ContractRegistry | Update contract addresses |
| `PUBLISHER_ROLE` | SecurityAudit, MerkleBatch | Log incidents |
| `AUDITOR_ROLE` | SecurityAudit | Query access |
| `POLICY_ADMIN_ROLE` | PolicyRegistry | Manage policies |
| `PROPOSER_ROLE` | Governance | Create proposals |
| `VOTER_ROLE` | Governance | Vote on proposals |
| `EXECUTOR_ROLE` | Governance | Execute approved proposals |
| `CURATOR_ROLE` | AddressBook | Manage watchlist |

---

## Deployment

### Deploy to Shardeum
```bash
npx hardhat run scripts/deploy-all.js --network shardeum
```

### Deploy to INCO
```bash
npx hardhat run scripts/deploy-all.js --network inco
```

### Addresses
After deployment, addresses are saved to:
```
deployments/ADDRESS_BOOK.json
```

---

## Off-Chain Integration

### Read from Registry
```javascript
const registry = new ethers.Contract(REGISTRY_ADDR, registryAbi, provider);
const auditAddr = await registry.getContract("SecurityAudit");
const audit = new ethers.Contract(auditAddr, auditAbi, signer);
```

### Log Incident
```javascript
const payload = JSON.stringify({txHash, decision, modelId, ts});
const incidentId = ethers.keccak256(ethers.toUtf8Bytes(payload));
await audit.logIncident(incidentId, actionCode, modelIdHash, riskScore);
```

### Batch Anchor (Merkle)
```javascript
// Off-chain: build Merkle tree from incident IDs
const root = merkleTree.getRoot();
await merkleBatch.anchorBatch(root, modelIdHash, incidentIds.length);
```

---

## Security Considerations

1. **Never store PII** - Only hashes and pointers
2. **Use multisig** - Deploy via Gnosis Safe for production
3. **Emit events** - Rich off-chain indexing, minimal on-chain storage
4. **Role separation** - PUBLISHER for nodes, ADMIN for governance
5. **Timelock** - Governance proposals have expiration

---

## ABIs

ABIs are generated after compilation:
```
artifacts/contracts/ContractRegistry.sol/ContractRegistry.json
artifacts/contracts/SecurityAudit.sol/SecurityAudit.json
...
```
