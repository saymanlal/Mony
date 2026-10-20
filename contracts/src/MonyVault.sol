// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract MonyVault is Ownable, Pausable, ReentrancyGuard {
    struct Goal {
        uint256 id;
        string name;
        uint256 target;
        uint256 balance;
        uint256 startTime;
        uint256 lockDuration;
        uint256 lastAccrueTime;
        uint256 accruedRewards;
        bool isClosed;
    }

    uint256 public constant SECONDS_PER_YEAR = 365 days;
    uint256 public constant BASIS_POINTS_DIVISOR = 10000;

    uint256 public rewardsPoolBalance;
    uint256 public totalDeposits;
    uint256 public penaltyBasisPoints = 500; // 5 percent default

    mapping(address => Goal[]) private userGoals;

    event GoalOpened(
        address indexed user,
        uint256 indexed goalId,
        string name,
        uint256 target,
        uint256 lockDuration
    );
    event GoalDeposited(address indexed user, uint256 indexed goalId, uint256 amount);
    event GoalWithdrawn(
        address indexed user,
        uint256 indexed goalId,
        uint256 amount,
        uint256 reward,
        uint256 penalty
    );
    event YieldAccrued(address indexed user, uint256 indexed goalId, uint256 accrued);
    event RewardsFunded(address indexed sender, uint256 amount);
    event PenaltyUpdated(uint256 oldPenalty, uint256 newPenalty);

    error GoalNotFound();
    error GoalAlreadyClosed();
    error ZeroDeposit();
    error InvalidGoalTarget();
    error PenaltyTooHigh();
    error TransferFailed();
    error InsufficientVaultBalance();

    constructor() Ownable(msg.sender) {}

    receive() external payable {
        depositRewards();
    }

    function depositRewards() public payable {
        if (msg.value == 0) revert ZeroDeposit();
        rewardsPoolBalance += msg.value;
        emit RewardsFunded(msg.sender, msg.value);
    }

    function setPenaltyBasisPoints(uint256 newPenaltyBps) external onlyOwner {
        if (newPenaltyBps > 5000) revert PenaltyTooHigh(); // max 50 percent
        uint256 old = penaltyBasisPoints;
        penaltyBasisPoints = newPenaltyBps;
        emit PenaltyUpdated(old, newPenaltyBps);
    }

    function getAprBps(uint256 lockDuration) public pure returns (uint256) {
        if (lockDuration >= 180 days) {
            return 1500; // 15 percent
        } else if (lockDuration >= 90 days) {
            return 1200; // 12 percent
        } else if (lockDuration >= 30 days) {
            return 800; // 8 percent
        } else {
            return 500; // 5 percent
        }
    }

    function openGoal(
        string calldata name,
        uint256 target,
        uint256 lockDuration
    ) external payable whenNotPaused returns (uint256 goalId) {
        if (target == 0) revert InvalidGoalTarget();

        goalId = userGoals[msg.sender].length;

        Goal memory newGoal = Goal({
            id: goalId,
            name: name,
            target: target,
            balance: msg.value,
            startTime: block.timestamp,
            lockDuration: lockDuration,
            lastAccrueTime: block.timestamp,
            accruedRewards: 0,
            isClosed: false
        });

        userGoals[msg.sender].push(newGoal);
        totalDeposits += msg.value;

        emit GoalOpened(msg.sender, goalId, name, target, lockDuration);
        if (msg.value > 0) {
            emit GoalDeposited(msg.sender, goalId, msg.value);
        }
    }

    function depositToGoal(uint256 goalId) external payable whenNotPaused {
        if (msg.value == 0) revert ZeroDeposit();
        if (goalId >= userGoals[msg.sender].length) revert GoalNotFound();

        Goal storage goal = userGoals[msg.sender][goalId];
        if (goal.isClosed) revert GoalAlreadyClosed();

        _accrueGoalYield(msg.sender, goalId);

        goal.balance += msg.value;
        totalDeposits += msg.value;

        emit GoalDeposited(msg.sender, goalId, msg.value);
    }

    function accrueYield(address user, uint256 goalId) external returns (uint256) {
        if (goalId >= userGoals[user].length) revert GoalNotFound();
        Goal storage goal = userGoals[user][goalId];
        if (goal.isClosed) revert GoalAlreadyClosed();
        return _accrueGoalYield(user, goalId);
    }

    function _accrueGoalYield(address user, uint256 goalId) internal returns (uint256 accrued) {
        Goal storage goal = userGoals[user][goalId];
        if (goal.isClosed || goal.balance == 0) {
            goal.lastAccrueTime = block.timestamp;
            return 0;
        }

        uint256 timeDelta = block.timestamp - goal.lastAccrueTime;
        if (timeDelta == 0) {
            return 0;
        }

        uint256 aprBps = getAprBps(goal.lockDuration);
        uint256 potentialYield = (goal.balance * aprBps * timeDelta) /
            (SECONDS_PER_YEAR * BASIS_POINTS_DIVISOR);

        accrued = potentialYield > rewardsPoolBalance ? rewardsPoolBalance : potentialYield;

        if (accrued > 0) {
            rewardsPoolBalance -= accrued;
            goal.accruedRewards += accrued;
            emit YieldAccrued(user, goalId, accrued);
        }

        goal.lastAccrueTime = block.timestamp;
    }

    function withdraw(uint256 goalId) external nonReentrant {
        if (goalId >= userGoals[msg.sender].length) revert GoalNotFound();
        Goal storage goal = userGoals[msg.sender][goalId];
        if (goal.isClosed) revert GoalAlreadyClosed();

        _accrueGoalYield(msg.sender, goalId);

        uint256 principal = goal.balance;
        uint256 rewards = goal.accruedRewards;
        uint256 penalty = 0;
        uint256 payout = 0;

        totalDeposits -= principal;
        goal.balance = 0;
        goal.accruedRewards = 0;
        goal.isClosed = true;

        bool isEarly = block.timestamp < (goal.startTime + goal.lockDuration);

        if (isEarly && goal.lockDuration > 0) {
            penalty = (principal * penaltyBasisPoints) / BASIS_POINTS_DIVISOR;
            payout = principal - penalty;
            rewardsPoolBalance += penalty + rewards;
            rewards = 0;
        } else {
            payout = principal + rewards;
        }

        if (address(this).balance < payout) revert InsufficientVaultBalance();

        emit GoalWithdrawn(msg.sender, goalId, payout, rewards, penalty);

        (bool success, ) = msg.sender.call{value: payout}("");
        if (!success) revert TransferFailed();
    }

    function getUserGoals(address user) external view returns (Goal[] memory) {
        return userGoals[user];
    }

    function getGoal(address user, uint256 goalId) external view returns (Goal memory) {
        if (goalId >= userGoals[user].length) revert GoalNotFound();
        return userGoals[user][goalId];
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }
}
