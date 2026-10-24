"""
EIP-712 signing utilities for MONY backend.

Signs two types of structured data:
  - Voucher: signed by VERIFIER_SIGNER_KEY, consumed by MonyTreasury.redeem
  - ExchangeQuote: signed by QUOTE_SIGNER_KEY, consumed by MonyExchange
"""

from __future__ import annotations

import time
from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data


# ------------------------------------------------------------------ #
# Voucher signing (used by scan / deposit flow)                       #
# ------------------------------------------------------------------ #

VOUCHER_TYPES: dict[str, Any] = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
        {"name": "verifyingContract", "type": "address"},
    ],
    "Voucher": [
        {"name": "user", "type": "address"},
        {"name": "amountWei", "type": "uint256"},
        {"name": "noteHash", "type": "bytes32"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiry", "type": "uint256"},
    ],
}

EXCHANGE_QUOTE_TYPES: dict[str, Any] = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
        {"name": "verifyingContract", "type": "address"},
    ],
    "ExchangeQuote": [
        {"name": "user", "type": "address"},
        {"name": "tokenIn", "type": "address"},
        {"name": "tokenOut", "type": "address"},
        {"name": "amountIn", "type": "uint256"},
        {"name": "amountOut", "type": "uint256"},
        {"name": "nonce", "type": "uint256"},
        {"name": "expiry", "type": "uint256"},
    ],
}


def _note_hash_bytes(note_hash: str) -> bytes:
    """Convert a 0x-prefixed or plain hex string to 32 bytes."""
    h = note_hash.removeprefix("0x")
    return bytes.fromhex(h.zfill(64))


class VoucherSigner:
    """Signs EIP-712 Vouchers for the MonyTreasury contract."""

    def __init__(self, private_key: str, treasury_address: str, chain_id: int) -> None:
        self._key = private_key
        self._treasury = treasury_address
        self._chain_id = chain_id
        self._nonce_counter = int(time.time())

    def sign_voucher(
        self,
        user_address: str,
        amount_wei: int,
        note_hash: str,
        expiry_offset_seconds: int = 300,
    ) -> dict[str, Any]:
        """Return a signed EIP-712 Voucher payload."""
        self._nonce_counter += 1
        nonce = self._nonce_counter
        expiry = int(time.time()) + expiry_offset_seconds

        eip712_data = {
            "types": VOUCHER_TYPES,
            "primaryType": "Voucher",
            "domain": {
                "name": "MonyTreasury",
                "version": "1",
                "chainId": self._chain_id,
                "verifyingContract": self._treasury,
            },
            "message": {
                "user": user_address,
                "amountWei": amount_wei,
                "noteHash": _note_hash_bytes(note_hash),
                "nonce": nonce,
                "expiry": expiry,
            },
        }

        signable = encode_typed_data(full_message=eip712_data)
        signed = Account.sign_message(signable, private_key=self._key)
        sig_hex = signed.signature.hex()
        if not sig_hex.startswith("0x"):
            sig_hex = "0x" + sig_hex

        return {
            "user": user_address,
            "amountWei": str(amount_wei),
            "noteHash": note_hash,
            "nonce": nonce,
            "expiry": expiry,
            "signature": sig_hex,
        }


class ExchangeQuoteSigner:
    """Signs EIP-712 ExchangeQuotes for the MonyExchange contract."""

    def __init__(self, private_key: str, exchange_address: str, chain_id: int) -> None:
        self._key = private_key
        self._exchange = exchange_address
        self._chain_id = chain_id
        self._nonce_counter = int(time.time()) + 1_000_000

    def sign_quote(
        self,
        user_address: str,
        token_in: str,
        token_out: str,
        amount_in: int,
        amount_out: int,
        expiry_offset_seconds: int = 60,
    ) -> dict[str, Any]:
        """Return a signed EIP-712 ExchangeQuote payload."""
        self._nonce_counter += 1
        nonce = self._nonce_counter
        expiry = int(time.time()) + expiry_offset_seconds

        eip712_data = {
            "types": EXCHANGE_QUOTE_TYPES,
            "primaryType": "ExchangeQuote",
            "domain": {
                "name": "MonyExchange",
                "version": "1",
                "chainId": self._chain_id,
                "verifyingContract": self._exchange,
            },
            "message": {
                "user": user_address,
                "tokenIn": token_in,
                "tokenOut": token_out,
                "amountIn": amount_in,
                "amountOut": amount_out,
                "nonce": nonce,
                "expiry": expiry,
            },
        }

        signable = encode_typed_data(full_message=eip712_data)
        signed = Account.sign_message(signable, private_key=self._key)
        sig_hex = signed.signature.hex()
        if not sig_hex.startswith("0x"):
            sig_hex = "0x" + sig_hex

        return {
            "user": user_address,
            "tokenIn": token_in,
            "tokenOut": token_out,
            "amountIn": str(amount_in),
            "amountOut": str(amount_out),
            "nonce": nonce,
            "expiry": expiry,
            "signature": sig_hex,
        }
