// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title MerkleBatchAnchor
 * @notice Gas-optimized batch anchoring for incident hashes
 * @dev Submit Merkle root instead of individual incidents
 * 
 * Flow:
 * 1. Collect N incident hashes off-chain
 * 2. Build Merkle tree, compute root
 * 3. Call anchorBatch(root, metadata) - single tx
 * 4. Store proofs off-chain for verification
 * 
 * Gas savings: ~21,000 gas per anchor vs ~50,000+ per individual log
 */
contract MerkleBatchAnchor is AccessControl {
    bytes32 public constant PUBLISHER_ROLE = keccak256("PUBLISHER_ROLE");
    
    // Events for off-chain indexing
    event BatchAnchored(
        bytes32 indexed root,
        bytes32 indexed modelId,
        uint256 batchSize,
        uint256 timestamp,
        address indexed reporter
    );
    
    event BatchVerified(bytes32 indexed root, bytes32 leaf, address verifier);
    
    // Minimal storage
    struct BatchInfo {
        uint256 timestamp;
        uint256 size;
        bytes32 modelId;
    }
    
    mapping(bytes32 => BatchInfo) public batches;  // root → info
    
    // Statistics
    uint256 public totalBatches;
    uint256 public totalIncidentsAnchored;
    
    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(PUBLISHER_ROLE, admin);
    }
    
    /**
     * @notice Anchor a batch of incidents via Merkle root
     * @param root Merkle root of incident hashes
     * @param modelId Model version identifier
     * @param batchSize Number of incidents in batch
     */
    function anchorBatch(
        bytes32 root,
        bytes32 modelId,
        uint256 batchSize
    ) external onlyRole(PUBLISHER_ROLE) {
        require(batches[root].timestamp == 0, "Already anchored");
        require(batchSize > 0 && batchSize <= 10000, "Invalid batch size");
        
        batches[root] = BatchInfo({
            timestamp: block.timestamp,
            size: batchSize,
            modelId: modelId
        });
        
        totalBatches++;
        totalIncidentsAnchored += batchSize;
        
        emit BatchAnchored(root, modelId, batchSize, block.timestamp, msg.sender);
    }
    
    /**
     * @notice Verify a leaf exists in an anchored batch
     * @param root Previously anchored Merkle root
     * @param leaf The incident hash to verify
     * @param proof Merkle proof (array of sibling hashes)
     */
    function verifyIncident(
        bytes32 root,
        bytes32 leaf,
        bytes32[] calldata proof
    ) external view returns (bool) {
        require(batches[root].timestamp > 0, "Batch not found");
        
        bytes32 computedHash = leaf;
        
        for (uint256 i = 0; i < proof.length; i++) {
            bytes32 proofElement = proof[i];
            
            if (computedHash <= proofElement) {
                computedHash = keccak256(abi.encodePacked(computedHash, proofElement));
            } else {
                computedHash = keccak256(abi.encodePacked(proofElement, computedHash));
            }
        }
        
        return computedHash == root;
    }
    
    /**
     * @notice Log verification event for audit trail
     */
    function recordVerification(bytes32 root, bytes32 leaf) external {
        require(batches[root].timestamp > 0, "Batch not found");
        emit BatchVerified(root, leaf, msg.sender);
    }
    
    /**
     * @notice Check if batch exists
     */
    function batchExists(bytes32 root) external view returns (bool) {
        return batches[root].timestamp > 0;
    }
    
    /**
     * @notice Get batch info
     */
    function getBatchInfo(bytes32 root) external view returns (
        uint256 timestamp,
        uint256 size,
        bytes32 modelId
    ) {
        BatchInfo memory info = batches[root];
        return (info.timestamp, info.size, info.modelId);
    }
    
    /**
     * @notice Get statistics
     */
    function getStats() external view returns (
        uint256 batchCount,
        uint256 totalIncidents
    ) {
        return (totalBatches, totalIncidentsAnchored);
    }
}
