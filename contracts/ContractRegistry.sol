// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title ContractRegistry
 * @notice Central registry for all NodesCrypt contract addresses
 * @dev Single source of truth - off-chain services read this to discover contracts
 * 
 * Key features:
 * - Stores addresses by name hash (e.g., keccak256("SecurityAudit"))
 * - Tracks version number for each contract
 * - Emits events for off-chain indexing
 * - RBAC: only ADMIN can update addresses
 */
contract ContractRegistry is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    
    // Events for off-chain indexing
    event ContractUpdated(
        bytes32 indexed nameHash,
        string name,
        address indexed addr,
        uint256 version,
        uint256 timestamp
    );
    event ContractRemoved(bytes32 indexed nameHash, string name, uint256 timestamp);
    
    // Minimal storage: name hash → address
    mapping(bytes32 => address) public contracts;
    mapping(bytes32 => uint256) public versions;
    mapping(bytes32 => string) public names;  // For human-readable lookup
    
    // List of registered contract names for enumeration
    bytes32[] public registeredContracts;
    
    constructor(address initialAdmin) {
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(ADMIN_ROLE, initialAdmin);
    }
    
    /**
     * @notice Register or update a contract address
     * @param name Human-readable contract name (e.g., "SecurityAudit")
     * @param addr Contract address
     */
    function setContract(string calldata name, address addr) external onlyRole(ADMIN_ROLE) {
        require(addr != address(0), "Invalid address");
        
        bytes32 nameHash = keccak256(bytes(name));
        
        // Track if this is a new registration
        bool isNew = contracts[nameHash] == address(0);
        
        contracts[nameHash] = addr;
        versions[nameHash] += 1;
        
        if (isNew) {
            names[nameHash] = name;
            registeredContracts.push(nameHash);
        }
        
        emit ContractUpdated(nameHash, name, addr, versions[nameHash], block.timestamp);
    }
    
    /**
     * @notice Get contract address by name
     * @param name Human-readable contract name
     */
    function getContract(string calldata name) external view returns (address) {
        return contracts[keccak256(bytes(name))];
    }
    
    /**
     * @notice Get contract address by name hash (more gas efficient)
     * @param nameHash keccak256 of contract name
     */
    function getContractByHash(bytes32 nameHash) external view returns (address) {
        return contracts[nameHash];
    }
    
    /**
     * @notice Get version of a contract
     */
    function getVersion(string calldata name) external view returns (uint256) {
        return versions[keccak256(bytes(name))];
    }
    
    /**
     * @notice Get count of registered contracts
     */
    function getContractCount() external view returns (uint256) {
        return registeredContracts.length;
    }
    
    /**
     * @notice Remove a contract from registry (soft delete - just zero address)
     */
    function removeContract(string calldata name) external onlyRole(ADMIN_ROLE) {
        bytes32 nameHash = keccak256(bytes(name));
        require(contracts[nameHash] != address(0), "Contract not found");
        
        contracts[nameHash] = address(0);
        emit ContractRemoved(nameHash, name, block.timestamp);
    }
}
