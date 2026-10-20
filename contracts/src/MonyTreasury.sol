// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";

contract MonyTreasury is Ownable, Pausable, ReentrancyGuard, EIP712 {
    using ECDSA for bytes32;

    struct Voucher {
        address user;
        uint256 amountWei;
        bytes32 noteHash;
        uint256 nonce;
        uint256 expiry;
    }

    struct DepositIntent {
        bytes32 voucherHash;
        uint256 nonce;
        uint256 expiry;
    }

    bytes32 public constant VOUCHER_TYPEHASH = keccak256(
        "Voucher(address user,uint256 amountWei,bytes32 noteHash,uint256 nonce,uint256 expiry)"
    );

    bytes32 public constant DEPOSIT_INTENT_TYPEHASH = keccak256(
        "DepositIntent(bytes32 voucherHash,uint256 nonce,uint256 expiry)"
    );

    address public verifierSigner;

    uint256 public maxDepositCap;
    uint256 public dailyUserCap;
    uint256 public dailyGlobalCap;

    mapping(bytes32 => bool) public usedNoteHashes;
    mapping(uint256 => bool) public usedVoucherNonces;
    mapping(uint256 => bool) public usedIntentNonces;

    mapping(address => mapping(uint256 => uint256)) public userDailyRedeemed;
    mapping(uint256 => uint256) public globalDailyRedeemed;

    event VerifierSignerUpdated(address indexed oldSigner, address indexed newSigner);
    event CapsUpdated(uint256 maxDepositCap, uint256 dailyUserCap, uint256 dailyGlobalCap);
    event Redeemed(
        address indexed user,
        uint256 amountWei,
        bytes32 indexed noteHash,
        uint256 nonce,
        bool manualMode
    );
    event FundsDeposited(address indexed sender, uint256 amount);
    event FundsWithdrawn(address indexed recipient, uint256 amount);

    error InvalidSigner();
    error VoucherExpired();
    error IntentExpired();
    error NoteAlreadyUsed();
    error VoucherNonceAlreadyUsed();
    error IntentNonceAlreadyUsed();
    error InvalidVerifierSignature();
    error InvalidUserSignature();
    error IntentVoucherMismatch();
    error ExceedsMaxDepositCap();
    error ExceedsDailyUserCap();
    error ExceedsDailyGlobalCap();
    error InsufficientTreasuryBalance();
    error TransferFailed();
    error ZeroAmount();
    error ZeroAddress();

    constructor(
        address initialVerifierSigner,
        uint256 initialMaxDepositCap,
        uint256 initialDailyUserCap,
        uint256 initialDailyGlobalCap
    ) Ownable(msg.sender) EIP712("MonyTreasury", "1") {
        if (initialVerifierSigner == address(0)) revert ZeroAddress();
        verifierSigner = initialVerifierSigner;
        maxDepositCap = initialMaxDepositCap;
        dailyUserCap = initialDailyUserCap;
        dailyGlobalCap = initialDailyGlobalCap;
    }

    receive() external payable {
        emit FundsDeposited(msg.sender, msg.value);
    }

    function hashVoucher(Voucher calldata voucher) public view returns (bytes32) {
        return _hashTypedDataV4(
            keccak256(
                abi.encode(
                    VOUCHER_TYPEHASH,
                    voucher.user,
                    voucher.amountWei,
                    voucher.noteHash,
                    voucher.nonce,
                    voucher.expiry
                )
            )
        );
    }

    function hashDepositIntent(DepositIntent calldata intent) public view returns (bytes32) {
        return _hashTypedDataV4(
            keccak256(
                abi.encode(
                    DEPOSIT_INTENT_TYPEHASH,
                    intent.voucherHash,
                    intent.nonce,
                    intent.expiry
                )
            )
        );
    }

    function redeem(
        Voucher calldata voucher,
        bytes calldata verifierSignature
    ) external nonReentrant whenNotPaused {
        bytes32 voucherDigest = hashVoucher(voucher);
        _verifyVerifierSignature(voucherDigest, verifierSignature);
        _processRedemption(voucher, false);
    }

    function redeemFor(
        Voucher calldata voucher,
        bytes calldata verifierSignature,
        DepositIntent calldata intent,
        bytes calldata userSignature
    ) external nonReentrant whenNotPaused {
        bytes32 voucherDigest = hashVoucher(voucher);
        _verifyVerifierSignature(voucherDigest, verifierSignature);

        if (intent.voucherHash != voucherDigest) revert IntentVoucherMismatch();
        if (block.timestamp > intent.expiry) revert IntentExpired();
        if (usedIntentNonces[intent.nonce]) revert IntentNonceAlreadyUsed();

        bytes32 intentDigest = hashDepositIntent(intent);
        address recoveredUser = ECDSA.recover(intentDigest, userSignature);
        if (recoveredUser != voucher.user) revert InvalidUserSignature();

        usedIntentNonces[intent.nonce] = true;

        _processRedemption(voucher, true);
    }

    function _verifyVerifierSignature(bytes32 digest, bytes calldata signature) internal view {
        address recovered = ECDSA.recover(digest, signature);
        if (recovered != verifierSigner) revert InvalidVerifierSignature();
    }

    function _processRedemption(Voucher calldata voucher, bool manualMode) internal {
        if (voucher.amountWei == 0) revert ZeroAmount();
        if (voucher.user == address(0)) revert ZeroAddress();
        if (block.timestamp > voucher.expiry) revert VoucherExpired();
        if (usedNoteHashes[voucher.noteHash]) revert NoteAlreadyUsed();
        if (usedVoucherNonces[voucher.nonce]) revert VoucherNonceAlreadyUsed();
        if (voucher.amountWei > maxDepositCap) revert ExceedsMaxDepositCap();

        uint256 currentDay = block.timestamp / 1 days;
        if (userDailyRedeemed[voucher.user][currentDay] + voucher.amountWei > dailyUserCap) {
            revert ExceedsDailyUserCap();
        }
        if (globalDailyRedeemed[currentDay] + voucher.amountWei > dailyGlobalCap) {
            revert ExceedsDailyGlobalCap();
        }
        if (address(this).balance < voucher.amountWei) {
            revert InsufficientTreasuryBalance();
        }

        usedNoteHashes[voucher.noteHash] = true;
        usedVoucherNonces[voucher.nonce] = true;
        userDailyRedeemed[voucher.user][currentDay] += voucher.amountWei;
        globalDailyRedeemed[currentDay] += voucher.amountWei;

        emit Redeemed(
            voucher.user,
            voucher.amountWei,
            voucher.noteHash,
            voucher.nonce,
            manualMode
        );

        (bool success, ) = voucher.user.call{value: voucher.amountWei}("");
        if (!success) revert TransferFailed();
    }

    function setVerifierSigner(address newSigner) external onlyOwner {
        if (newSigner == address(0)) revert ZeroAddress();
        address oldSigner = verifierSigner;
        verifierSigner = newSigner;
        emit VerifierSignerUpdated(oldSigner, newSigner);
    }

    function setCaps(
        uint256 newMaxDepositCap,
        uint256 newDailyUserCap,
        uint256 newDailyGlobalCap
    ) external onlyOwner {
        maxDepositCap = newMaxDepositCap;
        dailyUserCap = newDailyUserCap;
        dailyGlobalCap = newDailyGlobalCap;
        emit CapsUpdated(newMaxDepositCap, newDailyUserCap, newDailyGlobalCap);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function withdrawFunds(address payable recipient, uint256 amount) external nonReentrant onlyOwner {
        if (recipient == address(0)) revert ZeroAddress();
        if (amount > address(this).balance) revert InsufficientTreasuryBalance();
        emit FundsWithdrawn(recipient, amount);
        (bool success, ) = recipient.call{value: amount}("");
        if (!success) revert TransferFailed();
    }
}
