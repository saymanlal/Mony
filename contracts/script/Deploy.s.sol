// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/MonyTreasury.sol";
import "../src/MonyVault.sol";
import "../src/MonyExchange.sol";
import "../src/MockERC20.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerKey = vm.envOr(
            "DEPLOYER_PRIVATE_KEY",
            uint256(0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80)
        );
        address deployer = vm.addr(deployerKey);

        address verifierSigner = vm.envOr("VERIFIER_SIGNER_ADDRESS", deployer);
        address quoteSigner = vm.envOr("QUOTE_SIGNER_ADDRESS", deployer);

        vm.startBroadcast(deployerKey);

        // 1. Deploy Treasury
        MonyTreasury treasury = new MonyTreasury(
            verifierSigner,
            100 ether,  // maxDepositCap: 100 MON
            500 ether,  // dailyUserCap: 500 MON
            5000 ether  // dailyGlobalCap: 5000 MON
        );

        // 2. Deploy Vault
        MonyVault vault = new MonyVault();

        // 3. Deploy Exchange
        MonyExchange exchange = new MonyExchange(
            quoteSigner,
            1000 ether, // maxSwapAmount
            10000 ether // dailyLimit
        );

        // 4. Deploy Mock Tokens
        MockERC20 mUSDC = new MockERC20("Mock USD Coin", "mUSDC", 6);
        MockERC20 mDAI = new MockERC20("Mock Dai", "mDAI", 18);
        MockERC20 mWETH = new MockERC20("Mock Wrapped Ether", "mWETH", 18);
        MockERC20 mWBTC = new MockERC20("Mock Wrapped Bitcoin", "mWBTC", 8);

        // 5. Seed initial mock tokens liquidity to Exchange
        mUSDC.mint(address(exchange), 500_000 * 1e6);
        mDAI.mint(address(exchange), 500_000 * 1e18);
        mWETH.mint(address(exchange), 200 * 1e18);
        mWBTC.mint(address(exchange), 10 * 1e8);

        vm.stopBroadcast();

        // Build JSON output
        string memory json = "deployment";
        vm.serializeUint(json, "chainId", block.chainid);
        vm.serializeAddress(json, "treasury", address(treasury));
        vm.serializeAddress(json, "vault", address(vault));
        vm.serializeAddress(json, "exchange", address(exchange));
        vm.serializeAddress(json, "verifierSigner", verifierSigner);
        vm.serializeAddress(json, "quoteSigner", quoteSigner);

        string memory tokensJson = "tokens";
        vm.serializeAddress(tokensJson, "mUSDC", address(mUSDC));
        vm.serializeAddress(tokensJson, "mDAI", address(mDAI));
        vm.serializeAddress(tokensJson, "mWETH", address(mWETH));
        string memory tokenStr = vm.serializeAddress(tokensJson, "mWBTC", address(mWBTC));

        string memory finalJson = vm.serializeString(json, "tokens", tokenStr);

        string memory deploymentPath = "./deployments/monad-testnet.json";
        vm.writeJson(finalJson, deploymentPath);
    }
}
