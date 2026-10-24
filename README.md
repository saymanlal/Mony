# MONY

MONY is an Android payment application backed by computer vision banknote verification and smart contracts running on the Monad testnet (Chain ID: 10143). Users scan physical Indian rupee notes with their device camera, the backend verification engine inspects optical security features and duplicate records, and the equivalent value in MON is minted or released from a treasury contract into the user's non-custodial embedded wallet.

## Architecture and System Layout

```
├── app/                  # Expo React Native client (TypeScript, Expo Router)
│   ├── src/
│   │   ├── app/          # Navigation screens (Tabs, Deposit, Send, Receive, Save, Trade)
│   │   ├── components/   # Atomic UI system (Cards, Buttons, ScanReticle, Badges)
│   │   ├── services/     # Viem embedded wallet, API client, secure storage
│   │   └── store/        # Zustand state stores (Wallet, Operating Modes)
│   ├── app.config.ts     # Expo configuration
│   └── eas.json          # EAS Android build profile
├── backend/              # Python FastAPI backend & verification engine
│   ├── api/              # Endpoints (Scan, Deposit, Rates, Exchange, Analytics, Invoices)
│   ├── engine/           # Layers 0-5 verification engine (OpenCV headless, NumPy, Tesseract)
│   ├── profiles/         # RBI banknote security profiles (inr.json)
│   ├── db.py             # Async database abstraction (Supabase Postgres)
│   ├── rates.py          # CoinGecko rate client with stale-while-error fallback
│   ├── relayer.py        # Monad testnet relayer for automated redemptions
│   └── signer.py         # EIP-712 cryptographic voucher and quote signer
├── contracts/            # Foundry Solidity contracts
│   ├── src/
│   │   ├── MonyTreasury.sol  # Holds MON reserves, verifies EIP-712 vouchers and caps
│   │   ├── MonyVault.sol     # Savings goals, lock durations, and testnet yield accrual
│   │   ├── MonyExchange.sol  # Signed-quote token swap contract
│   │   └── MockERC20.sol     # Mock stablecoins and wrapped assets (mUSDC, mWETH, etc.)
│   ├── script/Deploy.s.sol   # Foundry deployment script
│   └── test/                 # Fuzz, unit, and invariant test suite
├── docs/                 # Architectural specifications and test reports
│   ├── ARCHITECTURE.md       # Threat models, crypto domains, protocol diagrams
│   ├── DEPLOYMENT.md         # Free deployment guide (Render, Supabase, Telegram APK)
│   ├── TEST_REPORT.md        # Three-run test matrix and verification benchmarks
│   └── VERIFICATION_REPORT.md# Computer vision confusion matrix and thresholds
├── reference/            # Genuine note reference templates and negative test vectors
└── scripts/              # Automation and operational scripts
    ├── deploy.sh             # Contract deployment script
    ├── fund_treasury.sh      # Treasury capital funding
    ├── seed.sh               # Liquidity seeding script
    ├── evaluate.py           # Verification engine benchmark evaluator
    └── e2e.ts                # Full end-to-end test execution
```

## Prerequisites

- Node.js 20.x or higher
- Python 3.12 with Tesseract OCR (`tesseract-ocr`, `tesseract-ocr-eng`) and OpenCV libraries
- Foundry (`forge`, `cast`)
- Docker (optional, for local container runs)

## Getting Started

### 1. Smart Contracts Setup

1. Navigate to contracts directory:
   ```bash
   cd contracts
   cp .env.example .env
   ```
2. Configure RPC and deployer keys in `.env`, then execute tests:
   ```bash
   forge test
   ```
3. Deploy to Monad testnet:
   ```bash
   ../scripts/deploy.sh
   ```

### 2. Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Apply database migrations to your Postgres/Supabase instance:
   ```bash
   psql "$DATABASE_URL" -f migrations/001_initial.sql
   ```
3. Run the backend test suite:
   ```bash
   pytest tests/ -v
   ```
4. Start the development server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 3. Mobile Application Setup

1. Navigate to app directory:
   ```bash
   cd app
   cp .env.example .env
   npm install
   ```
2. Run TypeScript type check:
   ```bash
   npm run type-check
   ```
3. Start Expo development server:
   ```bash
   npx expo start
   ```

## Operating Modes

MONY supports two redemption modes toggled from the Settings screen:
1. Automated Mode (Default): Upon banknote verification acceptance, the backend relayer automatically submits the EIP-712 voucher to the `MonyTreasury` contract. MON arrives in the user wallet without requiring manual interaction.
2. Manual Mode: The user must explicitly sign an EIP-712 `DepositIntent` payload with their local device key after biometric authentication. The relayer submits the `redeemFor` method containing both signatures.

## Verification Engine Layers

- Layer 0: Capture Integrity (Single-use HMAC challenge, device accelerometer and gyroscope motion validation).
- Layer 1: Medium Detection (FFT peak analysis for screen moire, halftone print screening detection, paper substrate micro-roughness).
- Layer 2: Geometry & Denomination (Contour perspective rectification, aspect ratio verification, color histogram, ORB matching).
- Layer 3: RBI Security Features (Windowed security thread color shift, watermark contrast, portrait template alignment).
- Layer 4: Serial & Duplicate Prevention (OCR validation, keccak256 salt-hashed unique registry, perceptual hash Hamming distance checks).
- Layer 5: Decision & Voucher (EIP-712 structured cryptographic authorization).

For comprehensive deployment steps, refer to `docs/DEPLOYMENT.md`.
