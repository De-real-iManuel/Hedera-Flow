// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BillingSettlement {
    address public owner;
    
    struct Bill {
        address user;
        address utility;
        uint256 amountHbar;
        uint256 amountFiat;
        string currency;
        bool paid;
        uint256 timestamp;
    }
    
    struct Dispute {
        bytes32 billId;
        address user;
        uint256 escrowAmount;
        bool resolved;
        address winner;
    }
    
    mapping(bytes32 => Bill) public bills;
    mapping(bytes32 => Dispute) public disputes;
    
    // Minimum transfer amounts in tinybars (1 HBAR = 100,000,000 tinybars)
    // Note: These are approximate minimums. The actual minimum is calculated
    // off-chain based on fiat equivalents (€5, $5, ₹50, R$10, ₦2000) and
    // current HBAR exchange rates. The contract enforces a safety minimum.
    uint256 public constant MIN_TRANSFER_HBAR = 5 * 100000000; // 5 HBAR safety minimum
    
    event BillPaid(
        bytes32 indexed billId,
        address indexed user,
        address indexed utility,
        uint256 amountHbar,
        string currency
    );
    
    event DisputeCreated(
        bytes32 indexed disputeId,
        bytes32 indexed billId,
        address indexed user,
        uint256 escrowAmount
    );
    
    event DisputeResolved(
        bytes32 indexed disputeId,
        address indexed winner,
        uint256 amount
    );
    
    constructor() {
        owner = msg.sender;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }
    
    function payBill(
        bytes32 billId,
        address utility,
        uint256 amountFiat,
        string memory currency
    ) external payable {
        // Enforce minimum transfer validation
        // The frontend calculates the HBAR amount based on fiat minimums:
        // - €5.00 (EUR) for Europe
        // - $5.00 (USD) for USA
        // - ₹50.00 (INR) for India
        // - R$10.00 (BRL) for Brazil
        // - ₦2,000 (NGN) for Nigeria
        // This contract enforces a safety minimum of 5 HBAR
        require(msg.value >= MIN_TRANSFER_HBAR, "Below minimum transfer amount");
        require(!bills[billId].paid, "Already paid");
        
        bills[billId] = Bill({
            user: msg.sender,
            utility: utility,
            amountHbar: msg.value,
            amountFiat: amountFiat,
            currency: currency,
            paid: true,
            timestamp: block.timestamp
        });
        
        (bool success, ) = payable(utility).call{value: msg.value}("");
        require(success, "Transfer failed");
        
        emit BillPaid(billId, msg.sender, utility, msg.value, currency);
    }
    
    function createDispute(
        bytes32 disputeId,
        bytes32 billId
    ) external payable {
        require(bills[billId].paid, "Bill not paid");
        require(bills[billId].user == msg.sender, "Not bill owner");
        require(!disputes[disputeId].resolved, "Already resolved");
        
        disputes[disputeId] = Dispute({
            billId: billId,
            user: msg.sender,
            escrowAmount: msg.value,
            resolved: false,
            winner: address(0)
        });
        
        emit DisputeCreated(disputeId, billId, msg.sender, msg.value);
    }
    
    function resolveDispute(
        bytes32 disputeId,
        address winner
    ) external onlyOwner {
        Dispute storage dispute = disputes[disputeId];
        require(!dispute.resolved, "Already resolved");
        require(dispute.escrowAmount > 0, "No escrow");
        
        dispute.resolved = true;
        dispute.winner = winner;
        
        uint256 amount = dispute.escrowAmount;
        (bool success, ) = payable(winner).call{value: amount}("");
        require(success, "Transfer failed");
        
        emit DisputeResolved(disputeId, winner, amount);
    }
    
    function getBill(bytes32 billId) external view returns (Bill memory) {
        return bills[billId];
    }
    
    function getDispute(bytes32 disputeId) external view returns (Dispute memory) {
        return disputes[disputeId];
    }
}
