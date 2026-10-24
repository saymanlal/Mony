# MONY Free Deployment Guide

This guide covers end-to-end deployment of MONY using free-tier services and sharing the resulting Android APK via Telegram.

## 1. Prerequisites and Free Accounts

Obtain the following free-tier accounts:
- GitHub: Repository hosting and CI/CD automated APK builds
- Supabase: Managed Postgres database (free tier)
- Render: Containerized backend hosting via Docker (free tier)
- Expo: Application build service (optional alternative to local EAS)
- 4 Throwaway EVM Wallets:
  1. Deployer Wallet (deploys contracts)
  2. Verifier Signer Wallet (signs EIP-712 verification vouchers)
  3. Relayer Wallet (broadcasts gasless transactions)
  4. Treasury Funder Wallet (funds MON reserves)

Never reuse production keys or funded mainnet wallets.

## 2. Fund Testnet Wallets

1. Visit the Monad testnet faucet: https://faucet.monad.xyz
2. Request testnet MON for the Deployer and Treasury Funder wallet addresses.
3. Confirm receipt on the Monad testnet explorer: https://testnet.monadexplorer.com

## 3. Deploy Smart Contracts

1. Copy contracts environment template:
   ```bash
   cp contracts/.env.example contracts/.env
   ```
2. Populate `contracts/.env` with:
   - `MONAD_RPC_URL=https://testnet-rpc.monad.xyz`
   - `DEPLOYER_PRIVATE_KEY=<your-deployer-private-key>`
   - `VERIFIER_SIGNER_ADDRESS=<your-verifier-address>`
   - `QUOTE_SIGNER_ADDRESS=<your-quote-signer-address>`

3. Run unit tests and deploy:
   ```bash
   cd contracts
   forge test
   ./scripts/deploy.sh
   ```
4. Deployment addresses are saved to `contracts/deployments/monad-testnet.json`.

5. Fund Treasury and Seed Liquidity:
   ```bash
   ./scripts/fund_treasury.sh 10ether
   ./scripts/seed.sh
   ```

## 4. Set Up Supabase Database

1. Create a new free project in the Supabase Dashboard.
2. In the Supabase SQL Editor, paste and execute the migration script:
   `backend/migrations/001_initial.sql`
3. Retrieve your Postgres connection URI from Project Settings -> Database -> Connection string (URI).

## 5. Deploy Backend to Render

1. Push your repository to GitHub.
2. In Render, select New -> Web Service -> Connect your GitHub repo.
3. Select "Docker" environment using `backend/Dockerfile` and root directory `backend`.
4. Choose the Free instance plan.
5. Configure Environment Variables:
   - `DATABASE_URL`: Your Supabase connection string
   - `MONAD_RPC_URL`: https://testnet-rpc.monad.xyz
   - `CHAIN_ID`: 10143
   - `TREASURY_ADDRESS`: Address from deployments JSON
   - `EXCHANGE_ADDRESS`: Address from deployments JSON
   - `VERIFIER_SIGNER_KEY`: Private key of verifier wallet
   - `RELAYER_KEY`: Private key of relayer wallet
   - `QUOTE_SIGNER_KEY`: Private key of quote signer wallet
   - `CHALLENGE_SECRET`: 64-character random hex string
   - `SERVER_SALT`: 32-character random hex string
   - `DEMO_INR_PER_MON`: 8500.0
   - `ALLOWED_ORIGINS`: *

6. Click Deploy. Once live, confirm health at `https://<your-service>.onrender.com/v1/health`.

## 6. Build Android APK

### Option A: Automated GitHub Actions Build (Recommended)
1. Add the following secrets to your GitHub repository (Settings -> Secrets and variables -> Actions):
   - `EXPO_TOKEN`: Your Expo account access token
   - `EXPO_PUBLIC_API_URL`: Your Render backend service URL
   - `EXPO_PUBLIC_TREASURY_ADDRESS`: Deployed Treasury contract address
   - `EXPO_PUBLIC_EXCHANGE_ADDRESS`: Deployed Exchange contract address

2. Push a version tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. The `android-apk.yml` workflow compiles the APK and attaches it to the GitHub Releases page.

### Option B: Local EAS Build
```bash
cd app
eas build --platform android --profile preview --local --output=./mony.apk
```

## 7. Distribute and Install via Telegram

1. Open Telegram on desktop or mobile.
2. Send `mony.apk` as an uncompressed document to your Telegram chat or Saved Messages.
3. On the recipient Android phone:
   - Open Telegram and tap `mony.apk`.
   - When prompted, enable "Allow from this source" in Android Install Unknown Apps settings.
   - If Google Play Protect displays an "Unrecognized app" notice, tap "More details" and select "Install anyway".

## 8. First-Run Acceptance Checklist

1. Launch MONY and create a new wallet.
2. Back up the 12-word recovery phrase and complete the 3-word verification quiz.
3. Confirm operating mode indicator in Settings (Automated vs Manual).
4. Initiate a Deposit scan using a reference banknote.
5. Verify on Monad explorer that MON balance arrives in the wallet.
6. Test Send flow by transferring a micro-amount to another address.
7. Open Savings Vault, fund a goal, and observe accrued yield.
8. Trade a small portion of MON for mUSDC.
9. Open Activity, select the transaction, and export an invoice PDF.
