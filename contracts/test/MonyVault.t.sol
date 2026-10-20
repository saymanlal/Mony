// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../src/MonyVault.sol";

contract MonyVaultTest is Test {
    MonyVault public vault;

    address internal owner = address(0xAA1);
    address internal alice = address(0xAA2);
    address internal bob = address(0xAA3);

    function setUp() public {
        vm.prank(owner);
        vault = new MonyVault();

        // Owner funds rewards pool with 10 ether
        vm.deal(owner, 20 ether);
        vm.prank(owner);
        vault.depositRewards{value: 10 ether}();

        vm.deal(alice, 50 ether);
        vm.deal(bob, 50 ether);
    }

    function test_OpenAndDepositGoal() public {
        vm.prank(alice);
        uint256 goalId = vault.openGoal{value: 5 ether}("College Fund", 10 ether, 30 days);

        assertEq(goalId, 0);
        MonyVault.Goal memory g = vault.getGoal(alice, 0);
        assertEq(g.balance, 5 ether);
        assertEq(g.target, 10 ether);
        assertEq(g.lockDuration, 30 days);
        assertFalse(g.isClosed);

        vm.prank(alice);
        vault.depositToGoal{value: 2 ether}(0);
        g = vault.getGoal(alice, 0);
        assertEq(g.balance, 7 ether);
        assertEq(vault.totalDeposits(), 7 ether);
    }

    function test_YieldAccrualAndUnlockWithdrawal() public {
        vm.prank(alice);
        uint256 goalId = vault.openGoal{value: 10 ether}("Car Savings", 10 ether, 365 days);

        // Advance time by 182.5 days (half a year)
        // APR for >= 180 days is 15% (1500 bps).
        // 10 ether * 15% / 2 = 0.75 ether expected reward
        vm.warp(block.timestamp + 182.5 days);

        uint256 accrued = vault.accrueYield(alice, goalId);
        assertApproxEqAbs(accrued, 0.75 ether, 0.01 ether);

        // Advance to full unlock (after 365 days)
        vm.warp(block.timestamp + 182.5 days + 1);

        uint256 aliceBalanceBefore = alice.balance;
        vm.prank(alice);
        vault.withdraw(goalId);

        // Should receive 10 ether principal + approx 1.5 ether reward
        assertApproxEqAbs(alice.balance - aliceBalanceBefore, 11.5 ether, 0.02 ether);
        MonyVault.Goal memory g = vault.getGoal(alice, goalId);
        assertTrue(g.isClosed);
        assertEq(g.balance, 0);
    }

    function test_EarlyWithdrawalPenalty() public {
        vm.prank(bob);
        uint256 goalId = vault.openGoal{value: 10 ether}("Locked Vacation", 10 ether, 90 days);

        // Withdraw before 90 days (at day 10)
        vm.warp(block.timestamp + 10 days);

        uint256 poolBefore = vault.rewardsPoolBalance();
        uint256 bobBefore = bob.balance;

        vm.prank(bob);
        vault.withdraw(goalId);

        // 5% penalty of 10 ether is 0.5 ether
        // Bob gets 9.5 ether
        assertEq(bob.balance - bobBefore, 9.5 ether);

        // Rewards pool receives the 0.5 ether penalty
        assertEq(vault.rewardsPoolBalance(), poolBefore + 0.5 ether);
    }

    function test_YieldCappedByRewardsPool() public {
        // Vault has 10 ether in rewards pool
        // A huge deposit is opened
        vm.deal(alice, 2000 ether);
        vm.prank(alice);
        uint256 goalId = vault.openGoal{value: 1000 ether}("Whale Vault", 1000 ether, 180 days);

        // Advance time 100 days: potential yield would be huge (approx 41 ether)
        vm.warp(block.timestamp + 100 days);

        vault.accrueYield(alice, goalId);
        MonyVault.Goal memory g = vault.getGoal(alice, goalId);

        // Accrued yield must be capped at 10 ether (the entire pool)
        assertEq(g.accruedRewards, 10 ether);
        assertEq(vault.rewardsPoolBalance(), 0);
    }

    function test_Invariant_BalanceCoversDepositsAndRewards() public {
        vm.prank(alice);
        vault.openGoal{value: 8 ether}("Goal 1", 10 ether, 30 days);

        vm.prank(bob);
        vault.openGoal{value: 12 ether}("Goal 2", 15 ether, 90 days);

        vm.warp(block.timestamp + 40 days);
        vault.accrueYield(alice, 0);
        vault.accrueYield(bob, 0);

        uint256 totalObligations = vault.totalDeposits() + vault.rewardsPoolBalance();
        assertGe(address(vault).balance, totalObligations);
    }

    function testFuzz_OpenAndWithdraw(uint256 amount, uint256 lockDuration) public {
        vm.assume(amount > 0.01 ether && amount <= 20 ether);
        vm.assume(lockDuration <= 365 days);

        vm.prank(alice);
        uint256 goalId = vault.openGoal{value: amount}("Fuzz Goal", amount, lockDuration);

        // Unlock
        vm.warp(block.timestamp + lockDuration + 1);

        uint256 balanceBefore = alice.balance;
        vm.prank(alice);
        vault.withdraw(goalId);

        assertGe(alice.balance, balanceBefore + amount);
    }
}
