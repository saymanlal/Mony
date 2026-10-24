# MONY Architecture

## Overview

MONY is a mobile-first application on the Monad testnet that converts physical Indian Rupee banknotes into on-chain native MON tokens. A camera-based multi-layer verification pipeline analyses a live video scan of the banknote; if verification passes, a backend verifier key signs an EIP-712 voucher that the smart contract checks before releasing funds.

The system comprises three loosely coupled components: a set of Solidity contracts, a Python verification backend, and a React Native mobile application.

---

## System Diagram

```
+---------------------------+         HTTPS/JSON          +----------------------------+
|   React Native App        | --------------------------> |   Python Backend (FastAPI) |
|   (Expo, viem)            |                             |   Render Web Service       |
|                           | <-------------------------- |   Dockerfile               |
|   - Camera scan           |   challenge nonce (HMAC)    |                            |
|   - Wallet (device-local) |   voucher + EIP-712 sig     |   BanknoteVerifier         |
|   - EIP-712 signing       |                             |   Layer 0  capture hmac    |
|   - redeemFor tx          |                             |   Layer 1  medium detect   |
+---------------------------+                             |   Layer 2  geometry        |
           |                                              |   Layer 3  security feats  |
           | eth_sendRawTransaction                       |   Layer 4  serial/hash     |
           v                                              |   Layer 5  decision+sign   |
+---------------------------+                             +----------------------------+
|   Monad Testnet (10143)   |                                         |
|                           |                                         | Supabase REST API
|   MonyTreasury            |                             +----------------------------+
|   MonyVault               |                             |   Supabase PostgreSQL      |
|   MonyExchange            |                             |   - note_hashes table      |
|   MockERC20 tokens        |                             |   - phash index            |
+---------------------------+                             +----------------------------+
```

---

## Component Overview

### Contracts (`contracts/src/`)

**MonyTreasury**

Accepts signed EIP-712 vouchers and releases MON to the user's address. The contract enforces:

- Per-voucher maximum deposit cap (`maxDepositCap`).
- Per-user daily cap (`dailyUserCap`) tracked by UTC day bucket.
- Global daily cap (`dailyGlobalCap`) across all users.
- Single-use note hash (`usedNoteHashes`) and single-use voucher nonce (`usedVoucherNonces`).
- The `redeemFor` path additionally checks a user-signed `DepositIntent` (EIP-712) that binds the voucher hash to a user nonce and expiry, preventing a third party from front-running the redemption.
- Emergency pause via `Ownable` + `Pausable`.
- Protected against reentrancy with `ReentrancyGuard`.

**MonyVault**

A savings vault that accepts MON deposits against named user goals with optional lock periods. Yield is accrued from a rewards pool funded by the contract owner. Early withdrawal triggers a configurable basis-point penalty, which is returned to the rewards pool.

**MonyExchange**

A quote-and-sweep DEX that executes swaps between native MON and any ERC-20 token (mUSDC, mDAI, mWETH, mWBTC) or between two ERC-20 tokens. Every swap requires an off-chain signed EIP-712 `Quote` struct that encodes the exact input and output amounts, token addresses, expiry, and a single-use nonce.

**MockERC20**

Minimal ERC-20 with a public `mint` function. Used only on testnet.

### Backend (`backend/engine/`)

A FastAPI service running in a Docker container on Render. All verification logic is stateless except for the note hash lookup against Supabase.

| Layer | File | Responsibility |
|-------|------|----------------|
| 0 | `layer0_capture.py` | HMAC challenge issuance and validation; frame-timing liveness check; accelerometer and gyroscope motion requirement |
| 1 | `layer1_medium.py` | 2D FFT moire detection; screen bezel edge detection; halftone rosette scoring; paper fibre variance |
| 2 | `layer2_geometry.py` | Contour rectification; aspect-ratio check; ORB feature matching against reference templates; colour histogram correlation; denomination consensus |
| 3 | `layer3_security.py` | Security thread localisation; tilt colour shift; watermark window contrast; microtext sharpness |
| 4 | `layer4_serial.py` | Dual-panel OCR via Tesseract; serial regex validation; Keccak-256 note hash derivation; perceptual hash near-duplicate check |
| 5 | `layer5_decision.py` | Weighted composite score; pass/rescan/reject decision; EIP-712 voucher signing with backend verifier key |

Verification configuration (thresholds, weights) is centralised in `config.py` and can be overridden at startup with environment variables.

### App (`app/`)

React Native application built with Expo. Key responsibilities:

- Camera capture session using the Expo Camera API; frames are uploaded to the backend as a multipart form alongside `CaptureMetadata` (nonce, timestamps, sensor samples).
- Device-local wallet: private key generated and stored in Expo SecureStore on first launch, never transmitted off-device.
- EIP-712 signing of the `DepositIntent` struct using viem.
- On-chain transactions via viem's JSON-RPC client pointed at the Monad testnet RPC.
- Exchange rate display with stale indicator; rates fetched from backend `/rates` endpoint.

---

## Security Model and Threat Model

### Replay Attacks

**Threat:** An attacker captures a valid voucher and replays it to receive a second payment.

**Mitigation:**
- The `Voucher` struct contains `nonce` (globally unique, marked used on first redeem) and `expiry` (a short TTL, typically 300 seconds from signing time).
- `noteHash` is derived from the serial number and denomination; it is stored permanently in `usedNoteHashes` on-chain.
- `redeemFor` additionally tracks `intentNonce` which is distinct from the voucher nonce.
- Supabase also stores note hashes for pre-chain duplicate detection.

### Forged Voucher

**Threat:** An attacker constructs a voucher with an arbitrary amount and submits it to the contract.

**Mitigation:**
- `MonyTreasury` recovers the signer from the EIP-712 digest and requires it to match `verifierSigner`.
- The verifier private key is held only in the backend environment (Render secret env var) and is never included in the mobile app binary or sent to the client.
- An attacker who does not possess the verifier key cannot produce a valid signature regardless of the voucher contents.

### Drained Treasury

**Threat:** A large number of deposits, or a single oversized deposit, drains the MON balance of `MonyTreasury`.

**Mitigation:**
- `maxDepositCap`: single voucher ceiling (default 100 MON).
- `dailyUserCap`: per-user daily ceiling (default 500 MON).
- `dailyGlobalCap`: total daily ceiling across all users (default 5000 MON).
- Owner can call `pause()` to halt all redemptions immediately.
- Owner can call `withdrawFunds()` to recover the treasury balance.

### Duplicate Note

**Threat:** The same physical banknote is scanned multiple times to obtain multiple deposits.

**Mitigation (primary, on-chain):** `noteHash` is recorded in `usedNoteHashes` after the first successful redemption. Any subsequent voucher for the same hash reverts with `NoteAlreadyUsed`.

**Mitigation (secondary, pre-chain):** Supabase stores the note hash and a perceptual hash (`phash`). Before signing a new voucher, the backend queries Supabase for an exact `noteHash` match and also checks perceptual Hamming distance against recent hashes. A near-duplicate (distance ≤ 6 bits) causes the scan to be rejected at the Layer 4 stage.

### Spoofed Camera Feed

**Threat:** An attacker photographs or displays a banknote image on a screen and presents it to the camera to pass verification.

**Mitigation:**
- Layer 0 issues a time-limited HMAC challenge nonce to the device. The nonce is single-use, has a 120-second TTL, and is embedded in the multipart upload. A pre-captured video cannot embed a nonce that is valid at replay time.
- Layer 1 specifically targets screen artefacts: 2D FFT moire patterns from pixel grids, screen bezel edge detection, halftone rosette scoring for printed photographs.
- Layer 0 additionally requires a minimum standard deviation of accelerometer and gyroscope readings across the capture session, confirming that the device was physically moving relative to the note during capture.

### Malicious Rate Data

**Threat:** A backend process or man-in-the-middle substitutes fraudulent exchange rate data, causing the app to display or execute swaps at incorrect rates.

**Mitigation:**
- The app fetches rates over HTTPS from its own backend endpoint.
- Rates carry a server timestamp; the app shows a "stale" indicator if the rate is older than a configurable threshold.
- Swap amounts are bounded per-transaction by `maxSwapAmount` and per-day by `dailyLimit` in `MonyExchange`.
- The signed `Quote` struct locks in exact input and output amounts at signing time; the contract enforces those exact amounts, so a rate change after signing cannot alter the executed swap.

### Key Theft

**Threat:** Compromise of the verifier signing key or the user's device wallet key.

**Mitigation (verifier key):**
- The verifier private key lives only in Render's secret environment variables.
- If compromised, the owner calls `setVerifierSigner(newAddress)` to rotate to a fresh key. All previously issued vouchers signed by the old key become invalid once the key is rotated.
- Contract caps limit economic exposure during the period before rotation is complete.

**Mitigation (device wallet):**
- The private key is generated on the device and stored in the OS secure enclave (Expo SecureStore).
- It is never transmitted to the backend or any third party.
- If a device is lost, the user's on-chain balance is determined by the chain state; there is no custodial recovery path.

---

## Data Flow Diagrams

### Deposit Flow

```
App                         Backend                      Chain
 |                              |                           |
 |-- POST /challenge ---------->|                           |
 |<- {nonce, hmac, expiry} -----|                           |
 |                              |                           |
 |  [User scans note]           |                           |
 |                              |                           |
 |-- POST /verify               |                           |
 |   (frames, metadata,         |                           |
 |    user_address, amount) --->|                           |
 |                              |-- Layer 0..5 pipeline ---|
 |                              |-- query Supabase phash   |
 |                              |-- sign EIP-712 Voucher   |
 |<- {voucher, signature} ------|                           |
 |                              |                           |
 |  [User signs DepositIntent]  |                           |
 |                              |                           |
 |-- eth_sendRawTransaction ----------------------------->  |
 |   redeemFor(voucher, sig,    |                           |
 |             intent, userSig) |                           |
 |                              |                    [checks sigs,
 |                              |                     caps, hashes]
 |<- tx receipt -------------------------------------------|
 |                              |                           |
 |  [balance updated]           |                           |
```

### Send Flow

```
App                                                  Chain
 |                                                     |
 |  [User enters recipient address and amount]         |
 |                                                     |
 |-- eth_sendRawTransaction (native MON transfer) -->  |
 |<- tx receipt --------------------------------------|
```

### Swap Flow

```
App                         Backend                      Chain
 |                              |                           |
 |-- GET /rates --------------->|                           |
 |<- {pairs, rates, ts} --------|                           |
 |                              |                           |
 |-- POST /quote                |                           |
 |   {tokenIn, tokenOut,        |                           |
 |    amountIn, user} --------->|                           |
 |                              |-- fetch live rate        |
 |                              |-- sign EIP-712 Quote     |
 |<- {quote, signature} --------|                           |
 |                              |                           |
 |-- eth_sendRawTransaction ----------------------------->  |
 |   swap(quote, signature)     |                           |
 |                              |              [verify sig, caps,
 |                              |               transfer tokens]
 |<- tx receipt -------------------------------------------|
```

---

## API Authentication Model

All backend endpoints follow a single authentication pattern: the backend verifies its own output (the HMAC challenge) and signs the result. There is no client authentication. The backend is intentionally designed to not require user credentials because:

1. The verification result is bound to `user_address` inside the EIP-712 struct, so a stolen voucher can only pay out to the address that was specified at signing time.
2. The contract enforces per-user daily caps, limiting the economic value of any signed voucher.

Endpoints:

| Method | Path | Auth requirement |
|--------|------|-----------------|
| POST | `/challenge` | None |
| POST | `/verify` | Valid HMAC nonce in request body |
| POST | `/quote` | None (amount caps enforced by contract) |
| GET | `/rates` | None |
| GET | `/health` | None |

---

## Deployment Architecture

```
GitHub (source)
  |
  |-- push tag v* --> GitHub Actions: android-apk.yml
  |                   (gradle assembleRelease, signed APK attached to Release)
  |
  |-- push main   --> GitHub Actions: contracts-test.yml (forge test)
  |                   GitHub Actions: backend-test.yml   (pytest)

Render (Web Service)
  - Dockerfile at backend/Dockerfile
  - Auto-deploy on push to main
  - Environment variables injected as secrets
  - 512 MB RAM free tier is sufficient for the verification engine

Supabase (PostgreSQL)
  - Managed PostgreSQL
  - Tables: note_hashes, phash_index
  - Row Level Security disabled (backend service role key only)
  - Free tier: 500 MB storage

Monad Testnet (chain ID 10143)
  - RPC: https://testnet-rpc.monad.xyz
  - Contracts deployed via Foundry forge script
  - Contract addresses stored in contracts/deployments/monad-testnet.json
```
