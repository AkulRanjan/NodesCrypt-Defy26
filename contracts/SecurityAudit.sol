// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title SecurityAudit
 * @notice Immutable incident anchor for NodesCrypt security decisions
 * @dev Minimal on-chain footprint - stores only hashes and timestamps
 * 
 * Key features:
 * - Stores incident hashes (not raw data)
 * - Emits rich events for off-chain indexing
 * - RBAC: PUBLISHER role for sidecars, AUDITOR for queries
 * - Never stores PII, IPs, or raw ML features
 * 
 * What gets logged:
 * - incidentId: SHA256 hash of decision payload
 * - action: 0=PASS, 1=DELAY, 2=DROP, 3=ESCALATE
 * - modelId: identifier of ML model version
 * - riskScore: 0-100 scale
 */
contract SecurityAudit is AccessControl {
    bytes32 public constant PUBLISHER_ROLE = keccak256("PUBLISHER_ROLE");
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");
    
    // Events for off-chain indexing (rich data, cheap storage)
    event IncidentLogged(
        bytes32 indexed incidentId,
        uint8 action,
        bytes32 indexed modelId,
        uint8 riskScore,
        uint256 timestamp,
        address indexed reporter
    );
    
    event ModelRegistered(bytes32 indexed modelId, string version, uint256 timestamp);
    
    // Minimal storage: only what's needed for verification
    mapping(bytes32 => uint256) public loggedAt;  // incidentId → timestamp
    
    // Statistics (public, no sensitive data)
    uint256 public totalIncidents;
    uint256 public lastIncidentTime;
    
    // Registered models (for audit trail)
    mapping(bytes32 => bool) public registeredModels;
    
    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(PUBLISHER_ROLE, admin);
        _grantRole(AUDITOR_ROLE, admin);
    }
    
    /**
     * @notice Log a security incident
     * @param incidentId Deterministic hash of incident payload
     * @param action RL action taken (0-3)
     * @param modelId Hash of model identifier
     * @param riskScore Calculated risk (0-100)
     */
    function logIncident(
        bytes32 incidentId,
        uint8 action,
        bytes32 modelId,
        uint8 riskScore
    ) external onlyRole(PUBLISHER_ROLE) {
        require(loggedAt[incidentId] == 0, "Already logged");
        require(action <= 3, "Invalid action");
        require(riskScore <= 100, "Invalid risk score");
        
        loggedAt[incidentId] = block.timestamp;
        totalIncidents++;
        lastIncidentTime = block.timestamp;
        
        emit IncidentLogged(
            incidentId,
            action,
            modelId,
            riskScore,
            block.timestamp,
            msg.sender
        );
    }
    
    /**
     * @notice Batch log multiple incidents (gas efficient)
     * @dev Use MerkleBatchAnchor for even more efficiency
     */
    function logIncidentBatch(
        bytes32[] calldata incidentIds,
        uint8[] calldata actions,
        bytes32 modelId,
        uint8[] calldata riskScores
    ) external onlyRole(PUBLISHER_ROLE) {
        require(incidentIds.length == actions.length, "Array mismatch");
        require(incidentIds.length == riskScores.length, "Array mismatch");
        require(incidentIds.length <= 50, "Max 50 per batch");
        
        for (uint256 i = 0; i < incidentIds.length; i++) {
            if (loggedAt[incidentIds[i]] == 0) {
                loggedAt[incidentIds[i]] = block.timestamp;
                totalIncidents++;
                
                emit IncidentLogged(
                    incidentIds[i],
                    actions[i],
                    modelId,
                    riskScores[i],
                    block.timestamp,
                    msg.sender
                );
            }
        }
        lastIncidentTime = block.timestamp;
    }
    
    /**
     * @notice Register a model version for audit trail
     */
    function registerModel(bytes32 modelId, string calldata version) 
        external onlyRole(PUBLISHER_ROLE) 
    {
        registeredModels[modelId] = true;
        emit ModelRegistered(modelId, version, block.timestamp);
    }
    
    /**
     * @notice Check if incident exists
     */
    function incidentExists(bytes32 incidentId) external view returns (bool) {
        return loggedAt[incidentId] > 0;
    }
    
    /**
     * @notice Get incident timestamp
     */
    function getIncidentTime(bytes32 incidentId) external view returns (uint256) {
        return loggedAt[incidentId];
    }
    
    /**
     * @notice Get audit statistics
     */
    function getStats() external view returns (
        uint256 total,
        uint256 lastTime
    ) {
        return (totalIncidents, lastIncidentTime);
    }
}
