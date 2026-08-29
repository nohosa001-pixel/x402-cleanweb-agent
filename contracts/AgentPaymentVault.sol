// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
}

/**
 * @title AgentPaymentVault
 * @notice On-chain pre-funded deposit vault for autonomous AI agents paying x402 micropayments.
 */
contract AgentPaymentVault {
    IERC20 public immutable usdcToken;
    address public treasuryWallet;
    address public owner;

    // Agent address => deposited USDC amount (6 decimals)
    mapping(address => uint256) public vaultBalances;

    event Deposited(address indexed agent, uint256 amount, uint256 newBalance);
    event Settled(address indexed agent, uint256 amount, address indexed treasury);
    event TreasuryUpdated(address previousTreasury, address newTreasury);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call");
        _;
    }

    constructor(address _usdcToken, address _treasuryWallet) {
        owner = msg.sender;
        usdcToken = IERC20(_usdcToken);
        treasuryWallet = _treasuryWallet;
    }

    function deposit(uint256 amount) external {
        require(amount > 0, "Deposit amount must be > 0");
        require(usdcToken.transferFrom(msg.sender, address(this), amount), "USDC transfer failed");

        vaultBalances[msg.sender] += amount;
        emit Deposited(msg.sender, amount, vaultBalances[msg.sender]);
    }

    function settleAgentBatch(address[] calldata agents, uint256[] calldata amounts) external onlyOwner {
        require(agents.length == amounts.length, "Mismatched arrays");

        uint256 totalToTreasury = 0;
        for (uint256 i = 0; i < agents.length; i++) {
            address agent = agents[i];
            uint256 amt = amounts[i];
            require(vaultBalances[agent] >= amt, "Insufficient balance");

            vaultBalances[agent] -= amt;
            totalToTreasury += amt;
            emit Settled(agent, amt, treasuryWallet);
        }

        if (totalToTreasury > 0) {
            require(usdcToken.transfer(treasuryWallet, totalToTreasury), "Treasury transfer failed");
        }
    }
}
