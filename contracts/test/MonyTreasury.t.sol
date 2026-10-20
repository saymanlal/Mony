// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../src/MonyTreasury.sol";

contract MaliciousReentrantReceiver {
    MonyTreasury public treasury;
    MonyTreasury.Voucher public secondVoucher;
    bytes public secondSignature;
    bool public hasAttacked;

    constructor(address _treasury) {
        treasury = MonyTreasury(payable(_treasury));
    }

    function setSecondAttack(
        MonyTreasury.Voucher calldata voucher,
        bytes calldata signature
    ) external {
        secondVoucher = voucher;
        secondSignature = signature;
    }

    receive() external payable {
        if (!hasAttacked && secondSignature.length > 0) {
            hasAttacked = true;
            treasury.redeem(secondVoucher, secondSignature);
        }
    }
}

contract MonyTreasuryTest is Test {
    MonyTreasury public treasury;

    uint256 internal ownerPrivateKey = 0xA11CE;
    uint256 internal verifierPrivateKey = 0xB0B;
    uint256 internal userPrivateKey = 0xCAFE;

    address internal owner;
    address internal verifierSigner;
    address internal user;

    uint256 internal constant MAX_DEPOSIT_CAP = 50 ether;
    uint256 internal constant DAILY_USER_CAP = 100 ether;
    uint256 internal constant DAILY_GLOBAL_CAP = 1000 ether;

    function setUp() public {
        owner = vm.addr(ownerPrivateKey);
        verifierSigner = vm.addr(verifierPrivateKey);
        user = vm.addr(userPrivateKey);

        vm.prank(owner);
        treasury = new MonyTreasury(
            verifierSigner,
            MAX_DEPOSIT_CAP,
            DAILY_USER_CAP,
            DAILY_GLOBAL_CAP
        );

        // Fund treasury with 500 ether
        vm.deal(owner, 500 ether);
        vm.prank(owner);
        payable(address(treasury)).transfer(500 ether);
    }

    function _signVoucher(
        MonyTreasury.Voucher memory voucher,
        uint256 pKey
    ) internal view returns (bytes memory) {
        bytes32 digest = treasury.hashVoucher(voucher);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pKey, digest);
        return abi.encodePacked(r, s, v);
    }

    function _signIntent(
        MonyTreasury.DepositIntent memory intent,
        uint256 pKey
    ) internal view returns (bytes memory) {
        bytes32 digest = treasury.hashDepositIntent(intent);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pKey, digest);
        return abi.encodePacked(r, s, v);
    }

    function test_RedeemAutomatedMode() public {
        bytes32 noteHash = keccak256(abi.encodePacked("NOTE-100-XYZ"));
        MonyTreasury.Voucher memory voucher = MonyTreasury.Voucher({
            user: user,
            amountWei: 5 ether,
            noteHash: noteHash,
            nonce: 1,
            expiry: block.timestamp + 300
        });

        bytes memory sig = _signVoucher(voucher, verifierPrivateKey);

        uint256 balanceBefore = user.balance;
        treasury.redeem(voucher, sig);
        assertEq(user.balance, balanceBefore + 5 ether);
        assertTrue(treasury.usedNoteHashes(noteHash));
        assertTrue(treasury.usedVoucherNonces(1));
    }

    function test_RedeemManualMode() public {
        bytes32 noteHash = keccak256(abi.encodePacked("NOTE-500-ABC"));
        MonyTreasury.Voucher memory voucher = MonyTreasury.Voucher({
            user: user,
            amountWei: 10 ether,
            noteHash: noteHash,
            nonce: 2,
            expiry: block.timestamp + 300
        });

        bytes memory verifierSig = _signVoucher(voucher, verifierPrivateKey);
        bytes32 voucherDigest = treasury.hashVoucher(voucher);

        MonyTreasury.DepositIntent memory intent = MonyTreasury.DepositIntent({
            voucherHash: voucherDigest,
            nonce: 101,
            expiry: block.timestamp + 300
        });
        bytes memory userSig = _signIntent(intent, userPrivateKey);

        uint256 balanceBefore = user.balance;
        treasury.redeemFor(voucher, verifierSig, intent, userSig);
        assertEq(user.balance, balanceBefore + 10 ether);
        assertTrue(treasury.usedNoteHashes(noteHash));
        assertTrue(treasury.usedIntentNonces(101));
    }

    function test_RejectDuplicateNoteHash() public {
        bytes32 noteHash = keccak256(abi.encodePacked("NOTE-DUPLICATE-TEST"));
        MonyTreasury.Voucher memory voucher1 = MonyTreasury.Voucher({
            user: user,
            amountWei: 2 ether,
            noteHash: noteHash,
            nonce: 3,
            expiry: block.timestamp + 300
        });
        bytes memory sig1 = _signVoucher(voucher1, verifierPrivateKey);
        treasury.redeem(voucher1, sig1);

        // Second attempt with same noteHash but different nonce
        MonyTreasury.Voucher memory voucher2 = MonyTreasury.Voucher({
            user: user,
            amountWei: 2 ether,
            noteHash: noteHash,
            nonce: 4,
            expiry: block.timestamp + 300
        });
        bytes memory sig2 = _signVoucher(voucher2, verifierPrivateKey);

        vm.expectRevert(MonyTreasury.NoteAlreadyUsed.selector);
        treasury.redeem(voucher2, sig2);
    }

    function test_RejectReusedNonce() public {
        bytes32 noteHash1 = keccak256(abi.encodePacked("NOTE-N1"));
        bytes32 noteHash2 = keccak256(abi.encodePacked("NOTE-N2"));

        MonyTreasury.Voucher memory voucher1 = MonyTreasury.Voucher({
            user: user,
            amountWei: 1 ether,
            noteHash: noteHash1,
            nonce: 5,
            expiry: block.timestamp + 300
        });
        bytes memory sig1 = _signVoucher(voucher1, verifierPrivateKey);
        treasury.redeem(voucher1, sig1);

        MonyTreasury.Voucher memory voucher2 = MonyTreasury.Voucher({
            user: user,
            amountWei: 1 ether,
            noteHash: noteHash2,
            nonce: 5, // reused nonce
            expiry: block.timestamp + 300
        });
        bytes memory sig2 = _signVoucher(voucher2, verifierPrivateKey);

        vm.expectRevert(MonyTreasury.VoucherNonceAlreadyUsed.selector);
        treasury.redeem(voucher2, sig2);
    }

    function test_RejectExpiredVoucher() public {
        MonyTreasury.Voucher memory voucher = MonyTreasury.Voucher({
            user: user,
            amountWei: 1 ether,
            noteHash: keccak256("EXPIRED"),
            nonce: 6,
            expiry: block.timestamp - 1
        });
        bytes memory sig = _signVoucher(voucher, verifierPrivateKey);

        vm.expectRevert(MonyTreasury.VoucherExpired.selector);
        treasury.redeem(voucher, sig);
    }

    function test_RejectInvalidVerifierSignature() public {
        MonyTreasury.Voucher memory voucher = MonyTreasury.Voucher({
            user: user,
            amountWei: 1 ether,
            noteHash: keccak256("BAD_SIG"),
            nonce: 7,
            expiry: block.timestamp + 300
        });
        // Signed with userPrivateKey instead of verifierPrivateKey
        bytes memory badSig = _signVoucher(voucher, userPrivateKey);

        vm.expectRevert(MonyTreasury.InvalidVerifierSignature.selector);
        treasury.redeem(voucher, badSig);
    }

    function test_RejectExceedsDepositCap() public {
        MonyTreasury.Voucher memory voucher = MonyTreasury.Voucher({
            user: user,
            amountWei: MAX_DEPOSIT_CAP + 1 ether,
            noteHash: keccak256("OVER_CAP"),
            nonce: 8,
            expiry: block.timestamp + 300
        });
        bytes memory sig = _signVoucher(voucher, verifierPrivateKey);

        vm.expectRevert(MonyTreasury.ExceedsMaxDepositCap.selector);
        treasury.redeem(voucher, sig);
    }

    function test_RejectExceedsDailyUserCap() public {
        // Daily user cap is 100 ether. Max single deposit is 50 ether.
        // Redeem two 50 ether deposits.
        bytes32 noteHash1 = keccak256("NOTE-C1");
        MonyTreasury.Voucher memory voucher1 = MonyTreasury.Voucher({
            user: user,
            amountWei: 50 ether,
            noteHash: noteHash1,
            nonce: 9,
            expiry: block.timestamp + 300
        });
        treasury.redeem(voucher1, _signVoucher(voucher1, verifierPrivateKey));

        bytes32 noteHash2 = keccak256("NOTE-C2");
        MonyTreasury.Voucher memory voucher2 = MonyTreasury.Voucher({
            user: user,
            amountWei: 50 ether,
            noteHash: noteHash2,
            nonce: 10,
            expiry: block.timestamp + 300
        });
        treasury.redeem(voucher2, _signVoucher(voucher2, verifierPrivateKey));

        // 3rd deposit should exceed daily user cap
        bytes32 noteHash3 = keccak256("NOTE-C3");
        MonyTreasury.Voucher memory voucher3 = MonyTreasury.Voucher({
            user: user,
            amountWei: 1 ether,
            noteHash: noteHash3,
            nonce: 11,
            expiry: block.timestamp + 300
        });
        bytes memory sig3 = _signVoucher(voucher3, verifierPrivateKey);

        vm.expectRevert(MonyTreasury.ExceedsDailyUserCap.selector);
        treasury.redeem(voucher3, sig3);
    }

    function test_SignerRotation() public {
        address newSigner = vm.addr(0x999);
        vm.prank(owner);
        treasury.setVerifierSigner(newSigner);
        assertEq(treasury.verifierSigner(), newSigner);

        MonyTreasury.Voucher memory voucher = MonyTreasury.Voucher({
            user: user,
            amountWei: 1 ether,
            noteHash: keccak256("ROTATED"),
            nonce: 12,
            expiry: block.timestamp + 300
        });

        // Old signer signature should fail
        bytes memory oldSig = _signVoucher(voucher, verifierPrivateKey);
        vm.expectRevert(MonyTreasury.InvalidVerifierSignature.selector);
        treasury.redeem(voucher, oldSig);

        // New signer signature succeeds
        bytes memory newSig = _signVoucher(voucher, 0x999);
        treasury.redeem(voucher, newSig);
    }

    function test_PauseBehavior() public {
        vm.prank(owner);
        treasury.pause();

        MonyTreasury.Voucher memory voucher = MonyTreasury.Voucher({
            user: user,
            amountWei: 1 ether,
            noteHash: keccak256("PAUSED"),
            nonce: 13,
            expiry: block.timestamp + 300
        });
        bytes memory sig = _signVoucher(voucher, verifierPrivateKey);

        vm.expectRevert(abi.encodeWithSignature("EnforcedPause()"));
        treasury.redeem(voucher, sig);

        vm.prank(owner);
        treasury.unpause();
        treasury.redeem(voucher, sig);
    }

    function test_ReentrancyAttemptRejected() public {
        MaliciousReentrantReceiver attacker = new MaliciousReentrantReceiver(address(treasury));
        bytes32 note1 = keccak256("REENTRANT-1");
        bytes32 note2 = keccak256("REENTRANT-2");

        MonyTreasury.Voucher memory v1 = MonyTreasury.Voucher({
            user: address(attacker),
            amountWei: 2 ether,
            noteHash: note1,
            nonce: 14,
            expiry: block.timestamp + 300
        });
        bytes memory sig1 = _signVoucher(v1, verifierPrivateKey);

        MonyTreasury.Voucher memory v2 = MonyTreasury.Voucher({
            user: address(attacker),
            amountWei: 2 ether,
            noteHash: note2,
            nonce: 15,
            expiry: block.timestamp + 300
        });
        bytes memory sig2 = _signVoucher(v2, verifierPrivateKey);

        attacker.setSecondAttack(v2, sig2);

        // When v1 executes, attacker receives MON and tries to re-enter with v2, which should fail due to ReentrancyGuard
        vm.expectRevert(MonyTreasury.TransferFailed.selector);
        treasury.redeem(v1, sig1);
    }

    function testFuzz_RedemptionWithinCaps(uint256 amount) public {
        vm.assume(amount > 0 && amount <= MAX_DEPOSIT_CAP);
        bytes32 noteHash = keccak256(abi.encodePacked("FUZZ", amount));

        MonyTreasury.Voucher memory voucher = MonyTreasury.Voucher({
            user: user,
            amountWei: amount,
            noteHash: noteHash,
            nonce: uint256(noteHash),
            expiry: block.timestamp + 300
        });

        bytes memory sig = _signVoucher(voucher, verifierPrivateKey);
        uint256 before = user.balance;
        treasury.redeem(voucher, sig);
        assertEq(user.balance, before + amount);
    }
}
