// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title PolicyRegistry
 * @notice Registry for NodesCrypt security policies
 * @dev Stores policy metadata on-chain, actual policies encrypted off-chain (INCO)
 * 
 * Key features:
 * - Store policy hashes (not full policies)
 * - Track policy status (active/paused/deprecated)
 * - Per-validator policy assignments
 * - Event-first design for indexing
 */
contract PolicyRegistry is AccessControl {
    bytes32 public constant POLICY_ADMIN_ROLE = keccak256("POLICY_ADMIN_ROLE");
    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");
    
    // Policy status enum
    enum PolicyStatus { INACTIVE, ACTIVE, PAUSED, DEPRECATED }
    
    // Policy metadata (minimal on-chain storage)
    struct Policy {
        bytes32 contentHash;      // Hash of encrypted policy content
        bytes32 encryptionKeyId;  // INCO key identifier
        PolicyStatus status;
        uint256 createdAt;
        uint256 updatedAt;
        string version;
    }
    
    // Events
    event PolicyCreated(
        bytes32 indexed policyId,
        bytes32 contentHash,
        string version,
        uint256 timestamp
    );
    
    event PolicyUpdated(
        bytes32 indexed policyId,
        bytes32 newContentHash,
        PolicyStatus status,
        uint256 timestamp
    );
    
    event PolicyAssigned(
        address indexed validator,
        bytes32 indexed policyId,
        uint256 timestamp
    );
    
    event GlobalPolicySet(bytes32 indexed policyId, uint256 timestamp);
    
    // Storage
    mapping(bytes32 => Policy) public policies;
    mapping(address => bytes32) public validatorPolicies;  // validator → policyId
    bytes32 public globalDefaultPolicy;
    
    bytes32[] public policyIds;  // For enumeration
    
    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(POLICY_ADMIN_ROLE, admin);
    }
    
    /**
     * @notice Create a new policy
     * @param policyId Unique policy identifier
     * @param contentHash Hash of encrypted policy content (stored in INCO)
     * @param encryptionKeyId INCO encryption key identifier
     * @param version Human-readable version string
     */
    function createPolicy(
        bytes32 policyId,
        bytes32 contentHash,
        bytes32 encryptionKeyId,
        string calldata version
    ) external onlyRole(POLICY_ADMIN_ROLE) {
        require(policies[policyId].createdAt == 0, "Policy exists");
        
        policies[policyId] = Policy({
            contentHash: contentHash,
            encryptionKeyId: encryptionKeyId,
            status: PolicyStatus.ACTIVE,
            createdAt: block.timestamp,
            updatedAt: block.timestamp,
            version: version
        });
        
        policyIds.push(policyId);
        
        emit PolicyCreated(policyId, contentHash, version, block.timestamp);
    }
    
    /**
     * @notice Update policy content hash
     */
    function updatePolicy(
        bytes32 policyId,
        bytes32 newContentHash,
        string calldata newVersion
    ) external onlyRole(POLICY_ADMIN_ROLE) {
        require(policies[policyId].createdAt > 0, "Policy not found");
        
        policies[policyId].contentHash = newContentHash;
        policies[policyId].version = newVersion;
        policies[policyId].updatedAt = block.timestamp;
        
        emit PolicyUpdated(policyId, newContentHash, policies[policyId].status, block.timestamp);
    }
    
    /**
     * @notice Set policy status
     */
    function setPolicyStatus(bytes32 policyId, PolicyStatus status) 
        external onlyRole(POLICY_ADMIN_ROLE) 
    {
        require(policies[policyId].createdAt > 0, "Policy not found");
        
        policies[policyId].status = status;
        policies[policyId].updatedAt = block.timestamp;
        
        emit PolicyUpdated(policyId, policies[policyId].contentHash, status, block.timestamp);
    }
    
    /**
     * @notice Assign policy to a validator
     */
    function assignPolicy(address validator, bytes32 policyId) 
        external onlyRole(POLICY_ADMIN_ROLE) 
    {
        require(policies[policyId].status == PolicyStatus.ACTIVE, "Policy not active");
        
        validatorPolicies[validator] = policyId;
        emit PolicyAssigned(validator, policyId, block.timestamp);
    }
    
    /**
     * @notice Set global default policy
     */
    function setGlobalDefaultPolicy(bytes32 policyId) 
        external onlyRole(POLICY_ADMIN_ROLE) 
    {
        require(policies[policyId].status == PolicyStatus.ACTIVE, "Policy not active");
        
        globalDefaultPolicy = policyId;
        emit GlobalPolicySet(policyId, block.timestamp);
    }
    
    /**
     * @notice Get effective policy for a validator
     * @dev Returns validator-specific policy if set, otherwise global default
     */
    function getEffectivePolicy(address validator) external view returns (bytes32) {
        bytes32 assigned = validatorPolicies[validator];
        if (assigned != bytes32(0) && policies[assigned].status == PolicyStatus.ACTIVE) {
            return assigned;
        }
        return globalDefaultPolicy;
    }
    
    /**
     * @notice Get policy content hash for off-chain retrieval
     */
    function getPolicyHash(bytes32 policyId) external view returns (bytes32) {
        return policies[policyId].contentHash;
    }
    
    /**
     * @notice Get full policy metadata
     */
    function getPolicy(bytes32 policyId) external view returns (
        bytes32 contentHash,
        bytes32 encryptionKeyId,
        PolicyStatus status,
        uint256 createdAt,
        uint256 updatedAt,
        string memory version
    ) {
        Policy memory p = policies[policyId];
        return (p.contentHash, p.encryptionKeyId, p.status, p.createdAt, p.updatedAt, p.version);
    }
    
    /**
     * @notice Get total policy count
     */
    function getPolicyCount() external view returns (uint256) {
        return policyIds.length;
    }
}
