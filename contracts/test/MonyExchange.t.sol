// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../src/MonyExchange.sol";
import "../src/MockERC20.sol";

contract MonyExchangeTest is Test {
    MonyExchange public exchange;
    MockERC20 public mUSDC;
    MockERC20 public mWBTC;

    uint256 internal ownerPrivateKey = 0xAA01;
    uint256 internal quoteSignerPrivateKey = 0xAA02;
    uint256 internal userPrivateKey = 0xAA03;

    address internal owner;
    address internal quoteSigner;
    address internal user;

    uint256 internal constant MAX_SWAP_AMOUNT = 500 ether;
    uint256 internal constant DAILY_LIMIT = 5000 ether;

    function setUp() public {
        owner = vm.addr(ownerPrivateKey);
        quoteSigner = vm.addr(quoteSignerPrivateKey);
        user = vm.addr(userPrivateKey);

        vm.startPrank(owner);
        exchange = new MonyExchange(quoteSigner, MAX_SWAP_AMOUNT, DAILY_LIMIT);

        mUSDC = new MockERC20("Mock USD Coin", "mUSDC", 6);
        mWBTC = new MockERC20("Mock Wrapped Bitcoin", "mWBTC", 8);

        // Mint liquidity to exchange
        mUSDC.mint(address(exchange), 100_000 * 1e6); // 100,000 mUSDC
        mWBTC.mint(address(exchange), 10 * 1e8); // 10 mWBTC

        // Mint tokens to user for testing swaps
        mUSDC.mint(user, 5_000 * 1e6);

        // Fund native MON liquidity to exchange
        vm.deal(owner, 100 ether);
        (bool ok, ) = address(exchange).call{value: 50 ether}("");
        require(ok, "Exchange fund failed");
        vm.stopPrank();

        vm.deal(user, 50 ether);

        vm.prank(user);
        mUSDC.approve(address(exchange), type(uint256).max);
    }

    function _signQuote(
        MonyExchange.Quote memory quote,
        uint256 pKey
    ) internal view returns (bytes memory) {
        bytes32 digest = exchange.hashQuote(quote);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pKey, digest);
        return abi.encodePacked(r, s, v);
    }

    function test_SwapNativeForERC20() public {
        // Swap 2 MON for 100 mUSDC (100 * 1e6)
        MonyExchange.Quote memory quote = MonyExchange.Quote({
            user: user,
            tokenIn: exchange.NATIVE_MON(),
            tokenOut: address(mUSDC),
            amountIn: 2 ether,
            amountOut: 100 * 1e6,
            expiry: block.timestamp + 300,
            nonce: 1
        });

        bytes memory sig = _signQuote(quote, quoteSignerPrivateKey);

        uint256 userUsdcBefore = mUSDC.balanceOf(user);
        vm.prank(user);
        exchange.swap{value: 2 ether}(quote, sig);

        assertEq(mUSDC.balanceOf(user), userUsdcBefore + 100 * 1e6);
        assertTrue(exchange.usedQuoteNonces(1));
    }

    function test_SwapERC20ForNative() public {
        // Swap 50 mUSDC for 1 MON
        MonyExchange.Quote memory quote = MonyExchange.Quote({
            user: user,
            tokenIn: address(mUSDC),
            tokenOut: exchange.NATIVE_MON(),
            amountIn: 50 * 1e6,
            amountOut: 1 ether,
            expiry: block.timestamp + 300,
            nonce: 2
        });

        bytes memory sig = _signQuote(quote, quoteSignerPrivateKey);

        uint256 userMonBefore = user.balance;
        vm.prank(user);
        exchange.swap(quote, sig);

        assertEq(user.balance, userMonBefore + 1 ether);
        assertTrue(exchange.usedQuoteNonces(2));
    }

    function test_RejectQuoteReplay() public {
        MonyExchange.Quote memory quote = MonyExchange.Quote({
            user: user,
            tokenIn: exchange.NATIVE_MON(),
            tokenOut: address(mUSDC),
            amountIn: 1 ether,
            amountOut: 50 * 1e6,
            expiry: block.timestamp + 300,
            nonce: 3
        });

        bytes memory sig = _signQuote(quote, quoteSignerPrivateKey);

        vm.prank(user);
        exchange.swap{value: 1 ether}(quote, sig);

        // Attempt replay
        vm.prank(user);
        vm.expectRevert(MonyExchange.QuoteNonceAlreadyUsed.selector);
        exchange.swap{value: 1 ether}(quote, sig);
    }

    function test_RejectExpiredQuote() public {
        MonyExchange.Quote memory quote = MonyExchange.Quote({
            user: user,
            tokenIn: exchange.NATIVE_MON(),
            tokenOut: address(mUSDC),
            amountIn: 1 ether,
            amountOut: 50 * 1e6,
            expiry: block.timestamp - 1,
            nonce: 4
        });

        bytes memory sig = _signQuote(quote, quoteSignerPrivateKey);

        vm.prank(user);
        vm.expectRevert(MonyExchange.QuoteExpired.selector);
        exchange.swap{value: 1 ether}(quote, sig);
    }

    function test_RejectInvalidQuoteSigner() public {
        MonyExchange.Quote memory quote = MonyExchange.Quote({
            user: user,
            tokenIn: exchange.NATIVE_MON(),
            tokenOut: address(mUSDC),
            amountIn: 1 ether,
            amountOut: 50 * 1e6,
            expiry: block.timestamp + 300,
            nonce: 5
        });

        // Signed by an unauthorized key
        bytes memory badSig = _signQuote(quote, 0xBADD);

        vm.prank(user);
        vm.expectRevert(MonyExchange.InvalidQuoteSignature.selector);
        exchange.swap{value: 1 ether}(quote, badSig);
    }

    function test_RejectSenderMismatch() public {
        MonyExchange.Quote memory quote = MonyExchange.Quote({
            user: user,
            tokenIn: exchange.NATIVE_MON(),
            tokenOut: address(mUSDC),
            amountIn: 1 ether,
            amountOut: 50 * 1e6,
            expiry: block.timestamp + 300,
            nonce: 6
        });

        bytes memory sig = _signQuote(quote, quoteSignerPrivateKey);

        // Another address calls swap with quote meant for user
        address mallory = address(0xDEAD);
        vm.deal(mallory, 2 ether);
        vm.prank(mallory);
        vm.expectRevert(MonyExchange.SenderNotQuoteUser.selector);
        exchange.swap{value: 1 ether}(quote, sig);
    }

    function test_RotateQuoteSigner() public {
        address newSigner = vm.addr(0x8888);
        vm.prank(owner);
        exchange.setQuoteSigner(newSigner);
        assertEq(exchange.quoteSigner(), newSigner);

        MonyExchange.Quote memory quote = MonyExchange.Quote({
            user: user,
            tokenIn: exchange.NATIVE_MON(),
            tokenOut: address(mUSDC),
            amountIn: 1 ether,
            amountOut: 50 * 1e6,
            expiry: block.timestamp + 300,
            nonce: 7
        });

        // Old key rejected
        bytes memory oldSig = _signQuote(quote, quoteSignerPrivateKey);
        vm.prank(user);
        vm.expectRevert(MonyExchange.InvalidQuoteSignature.selector);
        exchange.swap{value: 1 ether}(quote, oldSig);

        // New key accepted
        bytes memory newSig = _signQuote(quote, 0x8888);
        vm.prank(user);
        exchange.swap{value: 1 ether}(quote, newSig);
    }

    function test_PauseSwap() public {
        vm.prank(owner);
        exchange.pause();

        MonyExchange.Quote memory quote = MonyExchange.Quote({
            user: user,
            tokenIn: exchange.NATIVE_MON(),
            tokenOut: address(mUSDC),
            amountIn: 1 ether,
            amountOut: 50 * 1e6,
            expiry: block.timestamp + 300,
            nonce: 8
        });
        bytes memory sig = _signQuote(quote, quoteSignerPrivateKey);

        vm.prank(user);
        vm.expectRevert(abi.encodeWithSignature("EnforcedPause()"));
        exchange.swap{value: 1 ether}(quote, sig);

        vm.prank(owner);
        exchange.unpause();

        vm.prank(user);
        exchange.swap{value: 1 ether}(quote, sig);
    }
}
