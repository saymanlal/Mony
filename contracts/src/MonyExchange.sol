// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract MonyExchange is Ownable, Pausable, ReentrancyGuard, EIP712 {
    using SafeERC20 for IERC20;
    using ECDSA for bytes32;

    struct Quote {
        address user;
        address tokenIn;
        address tokenOut;
        uint256 amountIn;
        uint256 amountOut;
        uint256 expiry;
        uint256 nonce;
    }

    bytes32 public constant QUOTE_TYPEHASH = keccak256(
        "Quote(address user,address tokenIn,address tokenOut,uint256 amountIn,uint256 amountOut,uint256 expiry,uint256 nonce)"
    );

    address public constant NATIVE_MON = address(0);

    address public quoteSigner;
    uint256 public maxSwapAmount;
    uint256 public dailyLimit;

    mapping(uint256 => bool) public usedQuoteNonces;
    mapping(uint256 => uint256) public dailyVolume;

    event QuoteSignerUpdated(address indexed oldSigner, address indexed newSigner);
    event LimitsUpdated(uint256 maxSwapAmount, uint256 dailyLimit);
    event Swapped(
        address indexed user,
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        uint256 nonce
    );
    event LiquidityAdded(address indexed token, uint256 amount);
    event LiquidityWithdrawn(address indexed token, uint256 amount, address indexed to);

    error InvalidQuoteSigner();
    error QuoteExpired();
    error QuoteNonceAlreadyUsed();
    error InvalidQuoteSignature();
    error SenderNotQuoteUser();
    error InvalidInputAmount();
    error NativeAmountMismatch();
    error ExceedsMaxSwapAmount();
    error ExceedsDailyLimit();
    error InsufficientOutputLiquidity();
    error NativeTransferFailed();
    error ZeroAddress();
    error ZeroAmount();

    constructor(
        address initialQuoteSigner,
        uint256 initialMaxSwapAmount,
        uint256 initialDailyLimit
    ) Ownable(msg.sender) EIP712("MonyExchange", "1") {
        if (initialQuoteSigner == address(0)) revert ZeroAddress();
        quoteSigner = initialQuoteSigner;
        maxSwapAmount = initialMaxSwapAmount;
        dailyLimit = initialDailyLimit;
    }

    receive() external payable {
        emit LiquidityAdded(NATIVE_MON, msg.value);
    }

    function hashQuote(Quote calldata quote) public view returns (bytes32) {
        return _hashTypedDataV4(
            keccak256(
                abi.encode(
                    QUOTE_TYPEHASH,
                    quote.user,
                    quote.tokenIn,
                    quote.tokenOut,
                    quote.amountIn,
                    quote.amountOut,
                    quote.expiry,
                    quote.nonce
                )
            )
        );
    }

    function swap(
        Quote calldata quote,
        bytes calldata signature
    ) external payable nonReentrant whenNotPaused {
        if (msg.sender != quote.user) revert SenderNotQuoteUser();
        if (block.timestamp > quote.expiry) revert QuoteExpired();
        if (usedQuoteNonces[quote.nonce]) revert QuoteNonceAlreadyUsed();
        if (quote.amountIn == 0 || quote.amountOut == 0) revert ZeroAmount();

        if (maxSwapAmount > 0 && quote.amountIn > maxSwapAmount) {
            revert ExceedsMaxSwapAmount();
        }

        uint256 currentDay = block.timestamp / 1 days;
        if (dailyLimit > 0 && dailyVolume[currentDay] + quote.amountIn > dailyLimit) {
            revert ExceedsDailyLimit();
        }

        bytes32 digest = hashQuote(quote);
        address recoveredSigner = ECDSA.recover(digest, signature);
        if (recoveredSigner != quoteSigner) revert InvalidQuoteSignature();

        usedQuoteNonces[quote.nonce] = true;
        dailyVolume[currentDay] += quote.amountIn;

        // Inflow
        if (quote.tokenIn == NATIVE_MON) {
            if (msg.value != quote.amountIn) revert NativeAmountMismatch();
        } else {
            if (msg.value != 0) revert NativeAmountMismatch();
            IERC20(quote.tokenIn).safeTransferFrom(msg.sender, address(this), quote.amountIn);
        }

        emit Swapped(
            quote.user,
            quote.tokenIn,
            quote.tokenOut,
            quote.amountIn,
            quote.amountOut,
            quote.nonce
        );

        // Outflow
        if (quote.tokenOut == NATIVE_MON) {
            if (address(this).balance < quote.amountOut) revert InsufficientOutputLiquidity();
            (bool success, ) = quote.user.call{value: quote.amountOut}("");
            if (!success) revert NativeTransferFailed();
        } else {
            if (IERC20(quote.tokenOut).balanceOf(address(this)) < quote.amountOut) {
                revert InsufficientOutputLiquidity();
            }
            IERC20(quote.tokenOut).safeTransfer(quote.user, quote.amountOut);
        }
    }

    function addLiquidity(address token, uint256 amount) external payable onlyOwner {
        if (token == NATIVE_MON) {
            if (msg.value != amount) revert NativeAmountMismatch();
        } else {
            if (amount == 0) revert ZeroAmount();
            IERC20(token).safeTransferFrom(msg.sender, address(this), amount);
        }
        emit LiquidityAdded(token, amount);
    }

    function withdrawLiquidity(
        address token,
        uint256 amount,
        address payable to
    ) external nonReentrant onlyOwner {
        if (to == address(0)) revert ZeroAddress();
        if (amount == 0) revert ZeroAmount();

        emit LiquidityWithdrawn(token, amount, to);

        if (token == NATIVE_MON) {
            if (address(this).balance < amount) revert InsufficientOutputLiquidity();
            (bool success, ) = to.call{value: amount}("");
            if (!success) revert NativeTransferFailed();
        } else {
            IERC20(token).safeTransfer(to, amount);
        }
    }

    function setQuoteSigner(address newSigner) external onlyOwner {
        if (newSigner == address(0)) revert ZeroAddress();
        address old = quoteSigner;
        quoteSigner = newSigner;
        emit QuoteSignerUpdated(old, newSigner);
    }

    function setLimits(uint256 newMaxSwapAmount, uint256 newDailyLimit) external onlyOwner {
        maxSwapAmount = newMaxSwapAmount;
        dailyLimit = newDailyLimit;
        emit LimitsUpdated(newMaxSwapAmount, newDailyLimit);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }
}
