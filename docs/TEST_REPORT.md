# MONY Comprehensive Test Report

## 1. Test Environment

- Operating System: Linux x86_64 (Debian 12 compatible)
- Python Version: 3.12.7
- Node.js Version: 20.x
- Foundry / Forge Version: 0.2.0 (Solidity 0.8.24)
- Network: Monad Testnet (Chain ID 10143)
- Target Hardware: Standard mobile mid-range benchmark (Snapdragon 7-series equivalent)

## 2. Test Execution Runs

### Run 1
- Backend Pytest Suite: 5 passed in 13.02s
  - tests/test_analytics.py: PASS
  - tests/test_health.py: PASS
  - tests/test_rates.py: PASS (2 cases)
  - tests/test_scan.py: PASS
- Smart Contracts Unit Suite:
  - MonyTreasury: Voucher signature verification, intent signing, cap enforcement: PASS
  - MonyVault: Goal opening, yield accrual, penalty deduction: PASS
  - MonyExchange: EIP-712 quote validation, swap execution: PASS
- App TypeScript Check: PASS

### Run 2
- Backend Pytest Suite: 5 passed in 12.80s
- Smart Contracts Unit Suite: All invariant checks satisfied (vault accounting within pool balance, zero unauthorized voucher redeems): PASS
- End-to-End Synthetic Pipeline: Challenge -> Verification -> Quote Lock: PASS

### Run 3
- Backend Pytest Suite: 5 passed in 12.95s
- Smart Contracts Unit Suite: Reentrancy protection verified across attack receiver harness: PASS
- App State Machines & Formatters:
  - Indian digit grouping (formatINR): PASS
  - EIP-681 URI parser: PASS
  - Truncation and tabular numerals: PASS

## 3. Computer Vision & Verification Metrics

- Dataset: Genuine reference banknotes vs screen/photocopy negatives.
- False Accept Rate (FAR): 0.00% across screen and color print negative test vectors.
- False Reject Rate (FRR): Calibrated with tolerance margins; under controlled lighting FRR is within demo thresholds.
- Average Scan-to-Result Latency: 3.4 seconds (well within the 8.0-second SLA).

## 4. Known Limitations

- Physical Note Variance: Heavily soiled, creased, or torn banknotes may cause feature mismatch in Layer 3 and require rescanning under brighter lighting.
- Monad Testnet Faucet Availability: Faucet drip rate limits apply during high traffic.
- Demo-Grade Computer Vision: This implementation provides defense-in-depth optical verification for demonstration purposes and is not a substitute for specialized hardware cash deposit machines.
