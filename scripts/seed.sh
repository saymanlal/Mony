#!/usr/bin/env bash
set -euo pipefail

# Seed MONY Vault rewards and Exchange liquidity on Monad testnet

DEPLOYMENT_FILE="$(dirname "$0")/../contracts/deployments/monad-testnet.json"

if [ ! -f "$DEPLOYMENT_FILE" ]; then
    echo "Deployment file not found at $DEPLOYMENT_FILE"
    exit 1
fi

RPC_URL="${MONAD_RPC_URL:-https://testnet-rpc.monad.xyz}"
DEPLOYER_KEY="${DEPLOYER_PRIVATE_KEY:?Error: DEPLOYER_PRIVATE_KEY required}"

VAULT_ADDRESS=$(jq -r '.vault' "$DEPLOYMENT_FILE")
EXCHANGE_ADDRESS=$(jq -r '.exchange' "$DEPLOYMENT_FILE")

echo "Funding MonyVault rewards pool with 5 MON..."
cast send "$VAULT_ADDRESS" "depositRewards()" \
    --value 5ether \
    --rpc-url "$RPC_URL" \
    --private-key "$DEPLOYER_KEY"

echo "MonyVault rewards pool successfully seeded."
