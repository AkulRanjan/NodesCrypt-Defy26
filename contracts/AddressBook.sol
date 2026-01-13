// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title AddressBook
 * @notice Registry of monitored contracts and addresses
 * @dev Sidecars read this to prioritize scrutiny on high-risk addresses
 * 
 * Features:
 * - Store addresses with risk categories
 * - Label DEX pools, bridges, high-value contracts
 * - Off-chain nodes apply higher scrutiny to watched addresses
 */
contract AddressBook is AccessControl {
    bytes32 public constant CURATOR_ROLE = keccak256("CURATOR_ROLE");
    
    // Risk levels
    enum RiskLevel { UNKNOWN, LOW, MEDIUM, HIGH, CRITICAL }
    
    // Address entry
    struct WatchedAddress {
        RiskLevel riskLevel;
        bytes32 labelHash;      // keccak256 of label string
        bytes32 category;       // e.g., "DEX", "BRIDGE", "LENDING"
        bool isContract;
        uint256 addedAt;
        bool active;
    }
    
    // Events
    event AddressWatched(
        address indexed addr,
        RiskLevel riskLevel,
        bytes32 indexed category,
        bytes32 labelHash,
        uint256 timestamp
    );
    
    event AddressUpdated(
        address indexed addr,
        RiskLevel riskLevel,
        bool active,
        uint256 timestamp
    );
    
    event AddressRemoved(address indexed addr, uint256 timestamp);
    
    // Storage
    mapping(address => WatchedAddress) public watchedAddresses;
    address[] public addressList;
    
    // Category statistics
    mapping(bytes32 => uint256) public categoryCount;
    
    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(CURATOR_ROLE, admin);
    }
    
    /**
     * @notice Add an address to watchlist
     * @param addr Address to watch
     * @param riskLevel Risk category (0-4)
     * @param category Category hash (e.g., keccak256("DEX"))
     * @param label Human-readable label
     * @param isContract True if this is a contract address
     */
    function addAddress(
        address addr,
        RiskLevel riskLevel,
        bytes32 category,
        string calldata label,
        bool isContract
    ) external onlyRole(CURATOR_ROLE) {
        require(watchedAddresses[addr].addedAt == 0, "Already watched");
        
        bytes32 labelHash = keccak256(bytes(label));
        
        watchedAddresses[addr] = WatchedAddress({
            riskLevel: riskLevel,
            labelHash: labelHash,
            category: category,
            isContract: isContract,
            addedAt: block.timestamp,
            active: true
        });
        
        addressList.push(addr);
        categoryCount[category]++;
        
        emit AddressWatched(addr, riskLevel, category, labelHash, block.timestamp);
    }
    
    /**
     * @notice Update address risk level
     */
    function updateRiskLevel(address addr, RiskLevel newLevel) 
        external onlyRole(CURATOR_ROLE) 
    {
        require(watchedAddresses[addr].addedAt > 0, "Not found");
        
        watchedAddresses[addr].riskLevel = newLevel;
        
        emit AddressUpdated(addr, newLevel, watchedAddresses[addr].active, block.timestamp);
    }
    
    /**
     * @notice Deactivate an address (soft remove)
     */
    function deactivate(address addr) external onlyRole(CURATOR_ROLE) {
        require(watchedAddresses[addr].addedAt > 0, "Not found");
        
        watchedAddresses[addr].active = false;
        
        emit AddressRemoved(addr, block.timestamp);
    }
    
    /**
     * @notice Batch add addresses (gas efficient)
     */
    function addAddressBatch(
        address[] calldata addrs,
        RiskLevel[] calldata levels,
        bytes32 category
    ) external onlyRole(CURATOR_ROLE) {
        require(addrs.length == levels.length, "Array mismatch");
        require(addrs.length <= 100, "Max 100 per batch");
        
        for (uint256 i = 0; i < addrs.length; i++) {
            if (watchedAddresses[addrs[i]].addedAt == 0) {
                watchedAddresses[addrs[i]] = WatchedAddress({
                    riskLevel: levels[i],
                    labelHash: bytes32(0),
                    category: category,
                    isContract: true,
                    addedAt: block.timestamp,
                    active: true
                });
                
                addressList.push(addrs[i]);
                
                emit AddressWatched(addrs[i], levels[i], category, bytes32(0), block.timestamp);
            }
        }
        
        categoryCount[category] += addrs.length;
    }
    
    /**
     * @notice Check if address is watched
     */
    function isWatched(address addr) external view returns (bool) {
        return watchedAddresses[addr].active;
    }
    
    /**
     * @notice Get address risk level
     */
    function getRiskLevel(address addr) external view returns (RiskLevel) {
        return watchedAddresses[addr].riskLevel;
    }
    
    /**
     * @notice Get address details
     */
    function getAddress(address addr) external view returns (
        RiskLevel riskLevel,
        bytes32 labelHash,
        bytes32 category,
        bool isContract,
        bool active
    ) {
        WatchedAddress memory w = watchedAddresses[addr];
        return (w.riskLevel, w.labelHash, w.category, w.isContract, w.active);
    }
    
    /**
     * @notice Get total watched addresses
     */
    function getWatchedCount() external view returns (uint256) {
        return addressList.length;
    }
    
    /**
     * @notice Get addresses by category count
     */
    function getCategoryCount(bytes32 category) external view returns (uint256) {
        return categoryCount[category];
    }
}
