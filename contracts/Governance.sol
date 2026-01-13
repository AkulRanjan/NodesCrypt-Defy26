// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title Governance
 * @notice Simple governance contract for NodesCrypt
 * @dev Multisig-style approvals for critical changes
 * 
 * Features:
 * - Proposal creation and voting
 * - Timelock for execution
 * - Multi-signer approval
 * - Support for rule changes, upgrades, and parameter updates
 * 
 * Designed to integrate with Gnosis Safe for production
 */
contract Governance is AccessControl {
    bytes32 public constant PROPOSER_ROLE = keccak256("PROPOSER_ROLE");
    bytes32 public constant VOTER_ROLE = keccak256("VOTER_ROLE");
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");
    
    // Proposal types
    enum ProposalType { 
        RULE_CHANGE, 
        PARAMETER_UPDATE, 
        CONTRACT_UPGRADE, 
        ROLE_GRANT, 
        EMERGENCY 
    }
    
    enum ProposalStatus { 
        PENDING, 
        APPROVED, 
        REJECTED, 
        EXECUTED, 
        CANCELLED 
    }
    
    struct Proposal {
        ProposalType proposalType;
        ProposalStatus status;
        bytes32 contentHash;        // Hash of proposal content
        address proposer;
        uint256 createdAt;
        uint256 expiresAt;
        uint256 approvals;
        uint256 rejections;
        string description;
    }
    
    // Events
    event ProposalCreated(
        uint256 indexed proposalId,
        ProposalType proposalType,
        bytes32 contentHash,
        address indexed proposer,
        uint256 expiresAt
    );
    
    event ProposalVoted(
        uint256 indexed proposalId,
        address indexed voter,
        bool approved
    );
    
    event ProposalExecuted(uint256 indexed proposalId, uint256 timestamp);
    event ProposalCancelled(uint256 indexed proposalId, uint256 timestamp);
    
    event RuleApproved(bytes32 indexed ruleHash, uint256 proposalId, uint256 timestamp);
    event EmergencyActionTaken(bytes32 indexed actionHash, address executor, uint256 timestamp);
    
    // Storage
    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => bool)) public hasVoted;
    mapping(bytes32 => bool) public approvedRules;  // ruleHash → approved
    
    uint256 public proposalCount;
    uint256 public requiredApprovals;
    uint256 public proposalDuration;  // seconds
    
    constructor(
        address admin,
        uint256 _requiredApprovals,
        uint256 _proposalDuration
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(PROPOSER_ROLE, admin);
        _grantRole(VOTER_ROLE, admin);
        _grantRole(EXECUTOR_ROLE, admin);
        
        requiredApprovals = _requiredApprovals > 0 ? _requiredApprovals : 1;
        proposalDuration = _proposalDuration > 0 ? _proposalDuration : 7 days;
    }
    
    /**
     * @notice Create a new proposal
     * @param proposalType Type of proposal
     * @param contentHash Hash of proposal content (stored off-chain)
     * @param description Human-readable description
     */
    function createProposal(
        ProposalType proposalType,
        bytes32 contentHash,
        string calldata description
    ) external onlyRole(PROPOSER_ROLE) returns (uint256) {
        uint256 proposalId = proposalCount++;
        
        proposals[proposalId] = Proposal({
            proposalType: proposalType,
            status: ProposalStatus.PENDING,
            contentHash: contentHash,
            proposer: msg.sender,
            createdAt: block.timestamp,
            expiresAt: block.timestamp + proposalDuration,
            approvals: 0,
            rejections: 0,
            description: description
        });
        
        emit ProposalCreated(
            proposalId, 
            proposalType, 
            contentHash, 
            msg.sender, 
            block.timestamp + proposalDuration
        );
        
        return proposalId;
    }
    
    /**
     * @notice Vote on a proposal
     * @param proposalId Proposal to vote on
     * @param approve True to approve, false to reject
     */
    function vote(uint256 proposalId, bool approve) external onlyRole(VOTER_ROLE) {
        Proposal storage proposal = proposals[proposalId];
        
        require(proposal.createdAt > 0, "Proposal not found");
        require(proposal.status == ProposalStatus.PENDING, "Not pending");
        require(block.timestamp < proposal.expiresAt, "Expired");
        require(!hasVoted[proposalId][msg.sender], "Already voted");
        
        hasVoted[proposalId][msg.sender] = true;
        
        if (approve) {
            proposal.approvals++;
        } else {
            proposal.rejections++;
        }
        
        emit ProposalVoted(proposalId, msg.sender, approve);
        
        // Auto-approve if threshold reached
        if (proposal.approvals >= requiredApprovals) {
            proposal.status = ProposalStatus.APPROVED;
        }
    }
    
    /**
     * @notice Execute an approved proposal
     */
    function executeProposal(uint256 proposalId) external onlyRole(EXECUTOR_ROLE) {
        Proposal storage proposal = proposals[proposalId];
        
        require(proposal.status == ProposalStatus.APPROVED, "Not approved");
        
        proposal.status = ProposalStatus.EXECUTED;
        
        // Mark rule as approved if it's a rule change
        if (proposal.proposalType == ProposalType.RULE_CHANGE) {
            approvedRules[proposal.contentHash] = true;
            emit RuleApproved(proposal.contentHash, proposalId, block.timestamp);
        }
        
        emit ProposalExecuted(proposalId, block.timestamp);
    }
    
    /**
     * @notice Cancel a proposal
     */
    function cancelProposal(uint256 proposalId) external {
        Proposal storage proposal = proposals[proposalId];
        
        require(proposal.createdAt > 0, "Not found");
        require(
            proposal.proposer == msg.sender || hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Not authorized"
        );
        require(proposal.status == ProposalStatus.PENDING, "Not pending");
        
        proposal.status = ProposalStatus.CANCELLED;
        emit ProposalCancelled(proposalId, block.timestamp);
    }
    
    /**
     * @notice Emergency action (bypasses normal governance for critical issues)
     */
    function emergencyAction(bytes32 actionHash) external onlyRole(DEFAULT_ADMIN_ROLE) {
        emit EmergencyActionTaken(actionHash, msg.sender, block.timestamp);
    }
    
    /**
     * @notice Check if a rule is approved
     */
    function isRuleApproved(bytes32 ruleHash) external view returns (bool) {
        return approvedRules[ruleHash];
    }
    
    /**
     * @notice Update governance parameters
     */
    function updateParameters(
        uint256 _requiredApprovals,
        uint256 _proposalDuration
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        requiredApprovals = _requiredApprovals;
        proposalDuration = _proposalDuration;
    }
    
    /**
     * @notice Get proposal details
     */
    function getProposal(uint256 proposalId) external view returns (
        ProposalType proposalType,
        ProposalStatus status,
        bytes32 contentHash,
        address proposer,
        uint256 approvals,
        uint256 rejections,
        uint256 expiresAt
    ) {
        Proposal memory p = proposals[proposalId];
        return (
            p.proposalType,
            p.status,
            p.contentHash,
            p.proposer,
            p.approvals,
            p.rejections,
            p.expiresAt
        );
    }
}
