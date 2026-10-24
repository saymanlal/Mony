#!/usr/bin/env bash
set -euo pipefail

# Deploy MONY Smart Contracts to Monad Testnet

ENV_FILE="$(dirname "$0")/../contracts/.env"
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

RPC_URL="${MONAD_RPC_URL:-https://testnet-rpc.monad.xyz}"
DEPLOYER_KEY="${DEPLOYER_PRIVATE_KEY:?Error: DEPLOYER_PRIVATE_KEY environment variable required}"

echo "Deploying MONY contracts to Monad testnet ($RPC_URL)..."

cd "$(dirname "$0")/../contracts"
forge script script/Deploy.s.sol:DeployScript \
    --rpc-url "$RPC_URL" \
    --broadcast \
    --legacy

echo "Contracts deployment broadcast complete."
echo "Deployment manifest written to contracts/deployments/monad-testnet.json"
