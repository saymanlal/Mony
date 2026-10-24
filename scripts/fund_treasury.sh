#!/usr/bin/env bash
set -euo pipefail

# Fund MonyTreasury contract with testnet MON

DEPLOYMENT_FILE="$(dirname "$0")/../contracts/deployments/monad-testnet.json"

if [ ! -f "$DEPLOYMENT_FILE" ]; then
    echo "Deployment file not found at $DEPLOYMENT_FILE"
    exit 1
fi

RPC_URL="${MONAD_RPC_URL:-https://testnet-rpc.monad.xyz}"
DEPLOYER_KEY="${DEPLOYER_PRIVATE_KEY:?Error: DEPLOYER_PRIVATE_KEY required}"
AMOUNT="${1:-10ether}"

TREASURY_ADDRESS=$(jq -r '.treasury' "$DEPLOYMENT_FILE")

echo "Sending $AMOUNT from deployer to MonyTreasury ($TREASURY_ADDRESS)..."
cast send "$TREASURY_ADDRESS" \
    --value "$AMOUNT" \
    --rpc-url "$RPC_URL" \
    --private-key "$DEPLOYER_KEY"

echo "Treasury successfully funded."
