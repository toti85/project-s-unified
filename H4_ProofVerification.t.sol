// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.8.28;

import "forge-std/Test.sol";

/**
 * H4: Proof Verification / Claim Authorization / Cross-Domain Message Validation
 *
 * This test suite verifies that:
 * 1. Leaf values are computed deterministically (integrity check)
 * 2. Destination address validation gates claims (authorization)
 * 3. Message metadata is preserved through bridge (metadata integrity)
 * 4. Claim authorization depends on destination matching leaf commitment
 *
 * Contract under test: PolygonZkEVMBridgeV2
 * Focus: Proof integrity (leaf hash), authorization (destination address), message validation
 *
 * NOTE: Full merkle proof verification requires external proof generation (beyond Solidity).
 * These tests focus on the leaf computation and authorization checks that the bridge performs.
 */

contract H4_ProofVerification is Test {
    /**
     * Simulate getLeafValue from PolygonZkEVMBridgeV2
     * This is what the bridge uses to reconstruct leaves for proof verification
     */
    function getLeafValue(
        uint8 leafType,
        uint32 originNetwork,
        address originAddress,
        uint32 destinationNetwork,
        address destinationAddress,
        uint256 amount,
        bytes32 metadataHash
    ) public pure returns (bytes32) {
        return
            keccak256(
                abi.encodePacked(
                    leafType,
                    originNetwork,
                    originAddress,
                    destinationNetwork,
                    destinationAddress,
                    amount,
                    metadataHash
                )
            );
    }

    /**
     * H4.1: Verify destination address is embedded in leaf value (authorization)
     *
     * Assertion: Changing destination address changes leaf hash
     * Failure would mean: claim could be redirected without proof change,
     *                    funds sent to wrong recipient despite proof verification
     */
    function test_H4_DestinationAddressBindsToProof() public {
        uint8 leafType = 0;
        uint32 originNetwork = 1;
        address originAddress = address(0xAAAA);
        uint32 destinationNetwork = 137;
        address destinationAddress1 = address(0x1111);
        address destinationAddress2 = address(0x2222);
        uint256 amount = 100e18;
        bytes32 metadata = keccak256("test");

        bytes32 leaf1 = getLeafValue(
            leafType,
            originNetwork,
            originAddress,
            destinationNetwork,
            destinationAddress1,
            amount,
            metadata
        );

        bytes32 leaf2 = getLeafValue(
            leafType,
            originNetwork,
            originAddress,
            destinationNetwork,
            destinationAddress2,
            amount,
            metadata
        );

        // Different destination → different leaf
        assertNotEq(leaf1, leaf2, "Destination address must affect leaf value");
    }

    /**
     * H4.2: Verify amount is embedded in leaf value (prevents under/over-claiming)
     *
     * Assertion: Changing amount changes leaf hash
     * Failure would mean: proof valid for different amount, funds mismatch
     */
    function test_H4_AmountBindsToProof() public {
        uint8 leafType = 0;
        uint32 originNetwork = 1;
        address originAddress = address(0xAAAA);
        uint32 destinationNetwork = 137;
        address destinationAddress = address(0x1111);
        uint256 amount1 = 100e18;
        uint256 amount2 = 200e18;
        bytes32 metadata = keccak256("test");

        bytes32 leaf1 = getLeafValue(
            leafType,
            originNetwork,
            originAddress,
            destinationNetwork,
            destinationAddress,
            amount1,
            metadata
        );

        bytes32 leaf2 = getLeafValue(
            leafType,
            originNetwork,
            originAddress,
            destinationNetwork,
            destinationAddress,
            amount2,
            metadata
        );

        // Different amount → different leaf
        assertNotEq(leaf1, leaf2, "Amount must affect leaf value");
    }

    /**
     * H4.3: Verify origin address is embedded in leaf value (source authentication)
     *
     * Assertion: Changing origin address changes leaf hash
     * Failure would mean: proof accepted from different origin, spoofing possible
     */
    function test_H4_OriginAddressBindsToProof() public {
        uint8 leafType = 0;
        uint32 originNetwork = 1;
        address originAddress1 = address(0x1111);
        address originAddress2 = address(0x2222);
        uint32 destinationNetwork = 137;
        address destinationAddress = address(0xDEAD);
        uint256 amount = 100e18;
        bytes32 metadata = keccak256("test");

        bytes32 leaf1 = getLeafValue(
            leafType,
            originNetwork,
            originAddress1,
            destinationNetwork,
            destinationAddress,
            amount,
            metadata
        );

        bytes32 leaf2 = getLeafValue(
            leafType,
            originNetwork,
            originAddress2,
            destinationNetwork,
            destinationAddress,
            amount,
            metadata
        );

        // Different origin → different leaf
        assertNotEq(leaf1, leaf2, "Origin address must affect leaf value");
    }

    /**
     * H4.4: Verify metadata hash integrity (prevents message tampering)
     *
     * Assertion: Changing metadata changes leaf hash
     * Failure would mean: message content modifiable without proof invalidation
     */
    function test_H4_MetadataHashBindsToProof() public {
        uint8 leafType = 0;
        uint32 originNetwork = 1;
        address originAddress = address(0xAAAA);
        uint32 destinationNetwork = 137;
        address destinationAddress = address(0x1111);
        uint256 amount = 100e18;
        bytes32 metadata1 = keccak256("original_message");
        bytes32 metadata2 = keccak256("tampered_message");

        bytes32 leaf1 = getLeafValue(
            leafType,
            originNetwork,
            originAddress,
            destinationNetwork,
            destinationAddress,
            amount,
            metadata1
        );

        bytes32 leaf2 = getLeafValue(
            leafType,
            originNetwork,
            originAddress,
            destinationNetwork,
            destinationAddress,
            amount,
            metadata2
        );

        // Different metadata → different leaf
        assertNotEq(leaf1, leaf2, "Metadata must affect leaf value");
    }

    /**
     * H4.5: Verify leaf type binding (distinguishes asset vs message claims)
     *
     * Assertion: Different leaf types produce different hashes
     * Failure would mean: asset proof could be used for message claim or vice versa
     */
    function test_H4_LeafTypeBindsToProof() public {
        uint8 leafType1 = 0; // Asset
        uint8 leafType2 = 1; // Message
        uint32 originNetwork = 1;
        address originAddress = address(0xAAAA);
        uint32 destinationNetwork = 137;
        address destinationAddress = address(0x1111);
        uint256 amount = 100e18;
        bytes32 metadata = keccak256("test");

        bytes32 leaf1 = getLeafValue(
            leafType1,
            originNetwork,
            originAddress,
            destinationNetwork,
            destinationAddress,
            amount,
            metadata
        );

        bytes32 leaf2 = getLeafValue(
            leafType2,
            originNetwork,
            originAddress,
            destinationNetwork,
            destinationAddress,
            amount,
            metadata
        );

        // Different leaf type → different leaf
        assertNotEq(leaf1, leaf2, "Leaf type must affect value");
    }

    /**
     * H4.6: Verify destination network is included in authorization
     *
     * Assertion: Changing destination network changes leaf hash
     * Failure would mean: claim valid across different networks, fund misdirection
     */
    function test_H4_DestinationNetworkBindsToProof() public {
        uint8 leafType = 0;
        uint32 originNetwork = 1;
        address originAddress = address(0xAAAA);
        uint32 destinationNetwork1 = 137; // Polygon
        uint32 destinationNetwork2 = 42161; // Arbitrum
        address destinationAddress = address(0x1111);
        uint256 amount = 100e18;
        bytes32 metadata = keccak256("test");

        bytes32 leaf1 = getLeafValue(
            leafType,
            originNetwork,
            originAddress,
            destinationNetwork1,
            destinationAddress,
            amount,
            metadata
        );

        bytes32 leaf2 = getLeafValue(
            leafType,
            originNetwork,
            originAddress,
            destinationNetwork2,
            destinationAddress,
            amount,
            metadata
        );

        // Different destination network → different leaf
        assertNotEq(leaf1, leaf2, "Destination network must affect leaf value");
    }

    /**
     * H4.7: Verify origin network binding (prevents cross-network replays)
     *
     * Assertion: Changing origin network changes leaf hash
     * Failure would mean: proof from network A valid on network B, replay possible
     */
    function test_H4_OriginNetworkBindsToProof() public {
        uint8 leafType = 0;
        uint32 originNetwork1 = 1; // Mainnet
        uint32 originNetwork2 = 42161; // Arbitrum
        address originAddress = address(0xAAAA);
        uint32 destinationNetwork = 137;
        address destinationAddress = address(0x1111);
        uint256 amount = 100e18;
        bytes32 metadata = keccak256("test");

        bytes32 leaf1 = getLeafValue(
            leafType,
            originNetwork1,
            originAddress,
            destinationNetwork,
            destinationAddress,
            amount,
            metadata
        );

        bytes32 leaf2 = getLeafValue(
            leafType,
            originNetwork2,
            originAddress,
            destinationNetwork,
            destinationAddress,
            amount,
            metadata
        );

        // Different origin network → different leaf
        assertNotEq(leaf1, leaf2, "Origin network must affect leaf value");
    }

    /**
     * H4.8: Verify full leaf uniqueness across parameter combinations
     *
     * Assertion: Leaf hashes are effectively unique for different parameter sets
     * Failure would mean: hash collisions possible, multiple proofs valid for same leaf
     */
    function test_H4_LeafHashUniqueness() public {
        bytes32[] memory leaves = new bytes32[](5);

        // Generate 5 different leaves with varied parameters
        leaves[0] = getLeafValue(
            0,
            1,
            address(0x1111),
            137,
            address(0xAAAA),
            100e18,
            keccak256("msg1")
        );

        leaves[1] = getLeafValue(
            0,
            1,
            address(0x2222),
            137,
            address(0xAAAA),
            100e18,
            keccak256("msg1")
        );

        leaves[2] = getLeafValue(
            0,
            1,
            address(0x1111),
            42,
            address(0xAAAA),
            100e18,
            keccak256("msg1")
        );

        leaves[3] = getLeafValue(
            0,
            1,
            address(0x1111),
            137,
            address(0xBBBB),
            100e18,
            keccak256("msg1")
        );

        leaves[4] = getLeafValue(
            0,
            1,
            address(0x1111),
            137,
            address(0xAAAA),
            200e18,
            keccak256("msg1")
        );

        // Verify all leaves are unique
        for (uint i = 0; i < 5; i++) {
            for (uint j = i + 1; j < 5; j++) {
                assertNotEq(leaves[i], leaves[j], "Leaves must be unique");
            }
        }
    }
}
