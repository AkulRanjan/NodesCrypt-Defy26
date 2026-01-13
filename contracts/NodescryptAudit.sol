// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title NodescryptAudit
 * @dev On-chain audit trail for Nodescrypt security decisions
 * Compatible with Shardeum, Ethereum, and INCO networks
 */
contract NodescryptAudit {
    // ============================================
    // STRUCTS
    // ============================================
    
    struct Incident {
        bytes32 incidentId;      // SHA256 hash of incident payload
        uint8 action;            // 0=PASS, 1=DELAY, 2=DROP, 3=ESCALATE
        bytes32 modelId;         // Model version identifier
        uint256 timestamp;       // Block timestamp
        address reporter;        // Node that reported
    }
    
    // ============================================
    // STATE
    // ============================================
    
    mapping(bytes32 => Incident) public incidents;
    bytes32[] public incidentIds;
    
    mapping(address => bool) public authorizedNodes;
    address public admin;
    
    uint256 public totalIncidents;
    uint256 public totalDropped;
    uint256 public totalDelayed;
    
    // ============================================
    // EVENTS
    // ============================================
    
    event IncidentLogged(
        bytes32 indexed incidentId,
        uint8 action,
        bytes32 modelId,
        address indexed reporter,
        uint256 timestamp
    );
    
    event NodeAuthorized(address indexed node);
    event NodeRevoked(address indexed node);
    event AdminTransferred(address indexed oldAdmin, address indexed newAdmin);
    
    // ============================================
    // MODIFIERS
    // ============================================
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    modifier onlyAuthorized() {
        require(authorizedNodes[msg.sender] || msg.sender == admin, "Not authorized");
        _;
    }
    
    // ============================================
    // CONSTRUCTOR
    // ============================================
    
    constructor() {
        admin = msg.sender;
        authorizedNodes[msg.sender] = true;
    }
    
    // ============================================
    // ADMIN FUNCTIONS
    // ============================================
    
    function authorizeNode(address node) external onlyAdmin {
        authorizedNodes[node] = true;
        emit NodeAuthorized(node);
    }
    
    function revokeNode(address node) external onlyAdmin {
        authorizedNodes[node] = false;
        emit NodeRevoked(node);
    }
    
    function transferAdmin(address newAdmin) external onlyAdmin {
        require(newAdmin != address(0), "Invalid address");
        emit AdminTransferred(admin, newAdmin);
        admin = newAdmin;
        authorizedNodes[newAdmin] = true;
    }
    
    // ============================================
    // CORE FUNCTIONS
    // ============================================
    
    /**
     * @dev Log a security incident
     * @param incidentId SHA256 hash of incident payload
     * @param action Mitigation action taken (0=PASS, 1=DELAY, 2=DROP, 3=ESCALATE)
     * @param modelId Identifier of ML model used
     */
    function logIncident(
        bytes32 incidentId,
        uint8 action,
        bytes32 modelId
    ) external onlyAuthorized {
        require(incidents[incidentId].timestamp == 0, "Incident exists");
        require(action <= 3, "Invalid action");
        
        incidents[incidentId] = Incident({
            incidentId: incidentId,
            action: action,
            modelId: modelId,
            timestamp: block.timestamp,
            reporter: msg.sender
        });
        
        incidentIds.push(incidentId);
        totalIncidents++;
        
        if (action == 2) totalDropped++;
        if (action == 1) totalDelayed++;
        
        emit IncidentLogged(incidentId, action, modelId, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Batch log multiple incidents
     */
    function logIncidentBatch(
        bytes32[] calldata ids,
        uint8[] calldata actions,
        bytes32[] calldata modelIds
    ) external onlyAuthorized {
        require(ids.length == actions.length && actions.length == modelIds.length, "Length mismatch");
        
        for (uint i = 0; i < ids.length; i++) {
            if (incidents[ids[i]].timestamp == 0 && actions[i] <= 3) {
                incidents[ids[i]] = Incident({
                    incidentId: ids[i],
                    action: actions[i],
                    modelId: modelIds[i],
                    timestamp: block.timestamp,
                    reporter: msg.sender
                });
                
                incidentIds.push(ids[i]);
                totalIncidents++;
                
                if (actions[i] == 2) totalDropped++;
                if (actions[i] == 1) totalDelayed++;
                
                emit IncidentLogged(ids[i], actions[i], modelIds[i], msg.sender, block.timestamp);
            }
        }
    }
    
    // ============================================
    // VIEW FUNCTIONS
    // ============================================
    
    function getIncident(bytes32 incidentId) external view returns (
        uint8 action,
        bytes32 modelId,
        uint256 timestamp,
        address reporter
    ) {
        Incident memory inc = incidents[incidentId];
        return (inc.action, inc.modelId, inc.timestamp, inc.reporter);
    }
    
    function getIncidentCount() external view returns (uint256) {
        return incidentIds.length;
    }
    
    function getRecentIncidents(uint256 count) external view returns (bytes32[] memory) {
        uint256 len = incidentIds.length;
        if (count > len) count = len;
        
        bytes32[] memory recent = new bytes32[](count);
        for (uint i = 0; i < count; i++) {
            recent[i] = incidentIds[len - 1 - i];
        }
        return recent;
    }
    
    function getStats() external view returns (
        uint256 total,
        uint256 dropped,
        uint256 delayed
    ) {
        return (totalIncidents, totalDropped, totalDelayed);
    }
}
