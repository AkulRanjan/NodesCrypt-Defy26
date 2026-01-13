// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 * @title SecurityAudit
 * @notice Confidential security audit log for INCO network
 * @dev All state is encrypted and accessible only to authorized parties
 * 
 * What gets logged:
 * - Decision hash (incident ID)
 * - Action taken (0-3)
 * - Risk score (0-100)
 * - Timestamp
 * 
 * Never logged:
 * - IPs, wallet balances, raw ML features, mempool contents
 */
contract SecurityAudit {
    event IncidentLogged(bytes32 indexed incidentId, uint8 actionTaken, uint256 timestamp);
    event AuditQueried(bytes32 indexed incidentId, address querier);

    struct Incident {
        bytes32 incidentId;
        uint8 actionTaken;      // 0: NO_OP, 1: RAISE_FEE, 2: DEPRIORITIZE, 3: DEFENSIVE
        uint256 riskScore;      // 0-100 scale
        uint256 timestamp;
        bool exists;
    }

    // Private mapping - confidential on INCO
    mapping(bytes32 => Incident) private incidents;
    
    // Audit statistics (public)
    uint256 public totalIncidents;
    uint256 public lastIncidentTime;

    // Access control
    address public owner;
    mapping(address => bool) public authorizedAuditors;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyAuthorized() {
        require(msg.sender == owner || authorizedAuditors[msg.sender], "Not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Log a security incident
     * @param _incidentId Deterministic hash of the incident
     * @param _actionTaken RL action (0-3)
     * @param _riskScore Calculated risk score (0-100)
     */
    function logIncident(
        bytes32 _incidentId,
        uint8 _actionTaken,
        uint256 _riskScore
    ) external onlyAuthorized {
        require(!incidents[_incidentId].exists, "Incident already logged");
        require(_actionTaken <= 3, "Invalid action");
        require(_riskScore <= 100, "Invalid risk score");

        incidents[_incidentId] = Incident({
            incidentId: _incidentId,
            actionTaken: _actionTaken,
            riskScore: _riskScore,
            timestamp: block.timestamp,
            exists: true
        });

        totalIncidents++;
        lastIncidentTime = block.timestamp;

        emit IncidentLogged(_incidentId, _actionTaken, block.timestamp);
    }

    /**
     * @notice Retrieve an incident (confidential on INCO)
     * @param _incidentId The incident hash to query
     */
    function getIncident(bytes32 _incidentId)
        external
        view
        onlyAuthorized
        returns (Incident memory)
    {
        require(incidents[_incidentId].exists, "Incident not found");
        return incidents[_incidentId];
    }

    /**
     * @notice Check if an incident exists
     */
    function incidentExists(bytes32 _incidentId) external view returns (bool) {
        return incidents[_incidentId].exists;
    }

    /**
     * @notice Add an authorized auditor
     */
    function addAuditor(address _auditor) external onlyOwner {
        authorizedAuditors[_auditor] = true;
    }

    /**
     * @notice Remove an authorized auditor
     */
    function removeAuditor(address _auditor) external onlyOwner {
        authorizedAuditors[_auditor] = false;
    }

    /**
     * @notice Get audit statistics (public)
     */
    function getStats() external view returns (uint256 total, uint256 lastTime) {
        return (totalIncidents, lastIncidentTime);
    }
}
