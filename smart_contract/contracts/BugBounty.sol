// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title BugBounty
 * @dev A smart contract to manage bug bounty submissions and payouts, with basic access control and pausable functionality.
 */
contract BugBounty is Ownable, Pausable {
    struct BugReport {
        address reporter;
        string description;
        uint8 severity;
        bool approved;
        bool paid;
        bool payoutRequested;
    }

    struct Dispute {
        address reporter;
        string reason;
        bool resolved;
    }

    uint256 public nextReportId;
    mapping(uint256 => BugReport) public reports;
    mapping(uint256 => Dispute) public disputes;

    event BugReportSubmitted(uint256 indexed reportId, address indexed reporter, string description, uint8 severity);
    event DisputeRaised(uint256 indexed reportId, address indexed reporter, string reason);
    struct Payout {
        uint256 reportId;
        address recipient;
        uint256 amount;
        uint256 approvals;
        bool executed;
    }

    mapping(address => bool) public isCommitteeMember;
    uint256 public committeeMemberCount;
    uint256 public requiredApprovals;
    mapping(uint256 => Payout) public payouts;
    mapping(uint256 => mapping(address => bool)) public payoutApprovals;
    uint256 public nextPayoutId;

    event DisputeResolved(uint256 indexed reportId, address indexed resolver);
    event PayoutRequested(uint256 indexed payoutId, uint256 indexed reportId, address recipient, uint256 amount);
    event PayoutApproved(uint256 indexed payoutId, address indexed approver);
    event PayoutExecuted(uint256 indexed payoutId);

    constructor(address[] memory _committee, uint256 _requiredApprovals) Ownable(msg.sender) {
        require(_committee.length > 0, "Committee cannot be empty");
        require(_requiredApprovals > 0 && _requiredApprovals <= _committee.length, "Invalid number of required approvals");
        for (uint i = 0; i < _committee.length; i++) {
            require(_committee[i] != address(0), "Invalid committee member address");
            isCommitteeMember[_committee[i]] = true;
        }
        committeeMemberCount = _committee.length;
        requiredApprovals = _requiredApprovals;
        nextReportId = 1;
        nextPayoutId = 1;
    }

    /**
     * @notice Pauses all state-changing functions. Only callable by owner.
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses the contract. Only callable by owner.
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @notice Submit a bug report.
     * @param description Short description of the vulnerability.
     * @param severity A severity score (0-10) assigned by the scanner.
     */
    function submitBug(string calldata description, uint8 severity) external whenNotPaused {
        require(severity <= 10, "Severity must be 0-10");
        reports[nextReportId] = BugReport({
            reporter: msg.sender,
            description: description,
            severity: severity,
            approved: false,
            paid: false,
            payoutRequested: false
        });
        emit BugReportSubmitted(nextReportId, msg.sender, description, severity);
        nextReportId += 1;
    }

    /**
     * @notice Approve a reported bug.  Only callable by owner.
     * @param reportId ID of the report to approve.
     */
    function approveBug(uint256 reportId) external onlyOwner whenNotPaused {
        BugReport storage report = reports[reportId];
        require(!report.approved, "Already approved");
        report.approved = true;
    }

    /**
     * @notice Request a payout for an approved bug. Only callable by the owner.
     * @param reportId ID of the report to payout.
     */
    function requestPayout(uint256 reportId) external onlyOwner whenNotPaused {
        BugReport storage report = reports[reportId];
        require(report.approved, "Report not approved");
        require(!report.paid, "Report already paid");
        require(!report.payoutRequested, "Payout already requested for this report");

        report.payoutRequested = true;
        uint256 reward = (uint256(report.severity) * 1 ether) / 100;
        require(address(this).balance >= reward, "Insufficient contract balance for payout");

        Payout storage newPayout = payouts[nextPayoutId];
        newPayout.reportId = reportId;
        newPayout.recipient = report.reporter;
        newPayout.amount = reward;

        emit PayoutRequested(nextPayoutId, reportId, report.reporter, reward);
        nextPayoutId++;
    }

    /**
     * @notice Approve a pending payout. Only callable by committee members.
     * @param payoutId ID of the payout to approve.
     */
    function approvePayout(uint256 payoutId) external whenNotPaused {
        require(isCommitteeMember[msg.sender], "Only committee members can approve");

        Payout storage p = payouts[payoutId];
        require(!p.executed, "Payout has already been executed");
        require(!payoutApprovals[payoutId][msg.sender], "You have already approved this payout");

        payoutApprovals[payoutId][msg.sender] = true;
        p.approvals++;

        emit PayoutApproved(payoutId, msg.sender);
    }

    /**
     * @notice Executes a fully approved payout. Can be called by anyone.
     * @param payoutId ID of the payout to execute.
     */
    function executePayout(uint256 payoutId) external whenNotPaused {
        Payout storage p = payouts[payoutId];
        require(!p.executed, "Payout has already been executed");
        require(p.approvals >= requiredApprovals, "Not enough approvals to execute payout");

        p.executed = true;
        BugReport storage report = reports[p.reportId];
        report.paid = true;

        require(address(this).balance >= p.amount, "Insufficient funds to execute payout");
        (bool success, ) = p.recipient.call{value: p.amount}("");
        require(success, "Transfer failed");

        emit PayoutExecuted(payoutId);
    }

    /**
     * @notice Adds a new member to the committee. Only callable by the owner.
     * @param _member The address of the new committee member.
     */
    function addCommitteeMember(address _member) external onlyOwner {
        require(_member != address(0), "Invalid address");
        require(!isCommitteeMember[_member], "Address is already a committee member");
        isCommitteeMember[_member] = true;
        committeeMemberCount++;
    }

    /**
     * @notice Removes a member from the committee. Only callable by the owner.
     * @param _member The address of the committee member to remove.
     */
    function removeCommitteeMember(address _member) external onlyOwner {
        require(_member != address(0), "Invalid address");
        require(isCommitteeMember[_member], "Address is not a committee member");
        require(committeeMemberCount - 1 >= requiredApprovals, "Cannot have fewer members than required approvals");
        isCommitteeMember[_member] = false;
        committeeMemberCount--;
    }

    /**
     * @notice Sets the number of required approvals for payouts. Only callable by the owner.
     * @param _newCount The new number of required approvals.
     */
    function setRequiredApprovals(uint256 _newCount) external onlyOwner {
        require(_newCount > 0, "Required approvals must be greater than zero");
        require(_newCount <= committeeMemberCount, "Cannot require more approvals than committee members");
        requiredApprovals = _newCount;
    }

    /**
     * @notice Allow the contract to receive funds.  Bounty pool is funded via ETH transfers.
     */
    receive() external payable {}

    /**
     * @notice Raise a dispute for a bug report that was not approved.
     * @param reportId ID of the report to dispute.
     * @param reason The reason for the dispute.
     */
    function raiseDispute(uint256 reportId, string calldata reason) external whenNotPaused {
        BugReport storage report = reports[reportId];
        require(report.reporter != address(0), "Report does not exist");
        require(msg.sender == report.reporter, "Only the reporter can raise a dispute");
        require(!report.approved, "Cannot dispute an approved report");
        require(disputes[reportId].reporter == address(0), "Dispute already raised for this report");

        disputes[reportId] = Dispute({
            reporter: msg.sender,
            reason: reason,
            resolved: false
        });

        emit DisputeRaised(reportId, msg.sender, reason);
    }

    /**
     * @notice Resolve a dispute. Only callable by the owner.
     * @param reportId ID of the report whose dispute is to be resolved.
     * @param approveReport Whether to approve the bug report as part of the resolution.
     */
    function resolveDispute(uint256 reportId, bool approveReport) external onlyOwner whenNotPaused {
        require(disputes[reportId].reporter != address(0), "No dispute found for this report");
        require(!disputes[reportId].resolved, "Dispute already resolved");

        disputes[reportId].resolved = true;

        if (approveReport) {
            BugReport storage report = reports[reportId];
            require(!report.approved, "Report already approved");
            report.approved = true;
        }

        emit DisputeResolved(reportId, msg.sender);
    }
}
