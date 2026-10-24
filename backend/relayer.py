"""
On-chain relayer for MONY backend.

Submits redeem and redeemFor transactions to the MonyTreasury contract on
Monad testnet. Handles nonce management, gas estimation, and receipt waiting.
All keys are read exclusively from environment variables.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from web3 import AsyncWeb3
from web3.middleware import ExtraDataToPOAMiddleware

logger = logging.getLogger(__name__)

# Minimal ABI fragments needed by the relayer
TREASURY_ABI = [
    {
        "name": "redeem",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "amountWei", "type": "uint256"},
            {"name": "noteHash", "type": "bytes32"},
            {"name": "nonce", "type": "uint256"},
            {"name": "expiry", "type": "uint256"},
            {"name": "sig", "type": "bytes"},
        ],
        "outputs": [],
    },
    {
        "name": "redeemFor",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "user", "type": "address"},
            {"name": "amountWei", "type": "uint256"},
            {"name": "noteHash", "type": "bytes32"},
            {"name": "nonce", "type": "uint256"},
            {"name": "expiry", "type": "uint256"},
            {"name": "sig", "type": "bytes"},
        ],
        "outputs": [],
    },
]


def _note_hash_bytes32(note_hash: str) -> bytes:
    h = note_hash.removeprefix("0x")
    return bytes.fromhex(h.zfill(64))


class Relayer:
    """Submits treasury transactions and waits for on-chain confirmation."""

    def __init__(
        self,
        rpc_url: str,
        chain_id: int,
        treasury_address: str,
        relayer_private_key: str,
        receipt_timeout: int = 120,
        poll_interval: float = 2.0,
    ) -> None:
        self._rpc_url = rpc_url
        self._chain_id = chain_id
        self._treasury_address = AsyncWeb3.to_checksum_address(treasury_address)
        self._relayer_key = relayer_private_key
        self._receipt_timeout = receipt_timeout
        self._poll_interval = poll_interval

        self._w3: Optional[AsyncWeb3] = None
        self._account: Optional[Any] = None
        self._nonce_lock = asyncio.Lock()
        self._local_nonce: Optional[int] = None

    async def _get_web3(self) -> AsyncWeb3:
        if self._w3 is None:
            self._w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(self._rpc_url))
            self._w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            from eth_account import Account as EthAccount
            self._account = EthAccount.from_key(self._relayer_key)
        return self._w3

    async def _next_nonce(self, w3: AsyncWeb3) -> int:
        async with self._nonce_lock:
            chain_nonce = await w3.eth.get_transaction_count(
                self._account.address, "pending"
            )
            if self._local_nonce is None or chain_nonce > self._local_nonce:
                self._local_nonce = chain_nonce
            nonce = self._local_nonce
            self._local_nonce += 1
            return nonce

    async def _wait_for_receipt(self, w3: AsyncWeb3, tx_hash: str) -> dict:
        deadline = time.monotonic() + self._receipt_timeout
        while time.monotonic() < deadline:
            try:
                receipt = await w3.eth.get_transaction_receipt(tx_hash)
                if receipt is not None:
                    return dict(receipt)
            except Exception:
                pass
            await asyncio.sleep(self._poll_interval)
        raise TimeoutError(f"Receipt not found for {tx_hash} within {self._receipt_timeout}s")

    async def redeem_for(
        self,
        user_address: str,
        amount_wei: int,
        note_hash: str,
        nonce: int,
        expiry: int,
        signature: str,
    ) -> str:
        """
        Call MonyTreasury.redeemFor on behalf of a user.
        Returns the transaction hash.
        """
        w3 = await self._get_web3()
        contract = w3.eth.contract(
            address=self._treasury_address,
            abi=TREASURY_ABI,
        )

        sig_bytes = bytes.fromhex(signature.removeprefix("0x"))
        note_bytes32 = _note_hash_bytes32(note_hash)

        tx_nonce = await self._next_nonce(w3)
        gas_price = await w3.eth.gas_price

        fn = contract.functions.redeemFor(
            AsyncWeb3.to_checksum_address(user_address),
            amount_wei,
            note_bytes32,
            nonce,
            expiry,
            sig_bytes,
        )

        gas_estimate = await fn.estimate_gas({"from": self._account.address})
        gas_limit = int(gas_estimate * 1.25)

        tx = await fn.build_transaction(
            {
                "from": self._account.address,
                "nonce": tx_nonce,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "chainId": self._chain_id,
            }
        )

        signed_tx = self._account.sign_transaction(tx)
        tx_hash_bytes = await w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash = tx_hash_bytes.hex()
        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash

        logger.info("redeemFor submitted tx_hash=%s user=%s amount_wei=%s", tx_hash, user_address, amount_wei)

        receipt = await self._wait_for_receipt(w3, tx_hash)
        status = receipt.get("status", 0)
        if status != 1:
            raise RuntimeError(f"Transaction {tx_hash} reverted on-chain (status={status})")

        logger.info("redeemFor confirmed tx_hash=%s", tx_hash)
        return tx_hash
