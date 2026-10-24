import time
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel
from eth_account import Account
from eth_account.messages import encode_typed_data
from .config import EngineConfig, DEFAULT_CONFIG
from .layer0_capture import Layer0Result
from .layer1_medium import Layer1Result
from .layer2_geometry import Layer2Result
from .layer3_security import Layer3Result
from .layer4_serial import Layer4Result

class SignedVoucher(BaseModel):
    user: str
    amount_wei: str
    amount_mon: float
    denomination_inr: int
    note_hash: str
    nonce: int
    expiry: int
    signature: str

class VerificationDecision(BaseModel):
    decision: str  # ACCEPT, REJECT, RESCAN
    score: float
    reason_code: str
    human_reason: str
    user_hint: Optional[str]
    voucher: Optional[SignedVoucher]
    breakdown: Dict[str, Any]

class Layer5DecisionEngine:
    def __init__(self, verifier_private_key: str, treasury_address: str, chain_id: int = 10143, config: Optional[EngineConfig] = None):
        self.verifier_key = verifier_private_key
        self.treasury_address = treasury_address
        self.chain_id = chain_id
        self.config = config or DEFAULT_CONFIG
        self._nonce_counter = int(time.time())

    def evaluate(
        self,
        l0: Layer0Result,
        l1: Layer1Result,
        l2: Layer2Result,
        l3: Layer3Result,
        l4: Layer4Result,
        user_address: str,
        amount_wei: int,
        amount_mon: float,
        denomination_inr: int
    ) -> VerificationDecision:
        thresh = self.config.thresholds

        # 1. Check for immediate critical rejection
        if not l0.passed:
            return VerificationDecision(
                decision="REJECT",
                score=l0.score,
                reason_code=l0.reason_code,
                human_reason=f"Capture integrity failed: {l0.details.get('message', l0.reason_code)}",
                user_hint=None,
                voucher=None,
                breakdown={"layer0": l0.model_dump()}
            )

        # Immediate spoof / screen / print tripwire rejection
        if not l1.passed and l1.score < 0.50:
            return VerificationDecision(
                decision="REJECT",
                score=l1.score,
                reason_code=l1.reason_code,
                human_reason=f"Medium check failed: {l1.details.get('message', l1.reason_code)}",
                user_hint="Place a genuine physical banknote on a flat surface",
                voucher=None,
                breakdown={"layer0": l0.model_dump(), "layer1": l1.model_dump()}
            )

        # Duplicate noteHash or perceptual match rejection
        if not l4.passed and "DUPLICATE" in l4.reason_code:
            return VerificationDecision(
                decision="REJECT",
                score=0.0,
                reason_code=l4.reason_code,
                human_reason=f"Duplicate detected: {l4.details.get('message', l4.reason_code)}",
                user_hint="Each physical banknote can only be redeemed once",
                voucher=None,
                breakdown={"layer0": l0.model_dump(), "layer4": l4.model_dump()}
            )

        # 2. Compute weighted composite score
        weights = [
            thresh.weight_layer1,
            thresh.weight_layer2,
            thresh.weight_layer3,
            thresh.weight_layer4
        ]
        layer_scores = [l1.score, l2.score, l3.score, l4.score]
        composite_score = float(sum(w * s for w, s in zip(weights, layer_scores)))

        # Check for minimum per-layer criteria
        layers_all_passed = (
            l1.passed and
            l2.passed and
            l3.passed and
            l4.passed
        )

        breakdown = {
            "layer0": l0.model_dump(),
            "layer1": l1.model_dump(),
            "layer2": l2.model_dump(),
            "layer3": l3.model_dump(),
            "layer4": l4.model_dump(),
            "composite_score": round(composite_score, 4)
        }

        # ACCEPT condition
        if composite_score >= thresh.overall_pass_threshold and layers_all_passed:
            voucher = self._create_signed_voucher(
                user_address=user_address,
                amount_wei=amount_wei,
                amount_mon=amount_mon,
                denomination_inr=denomination_inr,
                note_hash=l4.note_hash
            )
            return VerificationDecision(
                decision="ACCEPT",
                score=round(composite_score, 4),
                reason_code="VERIFICATION_PASSED",
                human_reason="Banknote verified as genuine and approved for redemption",
                user_hint=None,
                voucher=voucher,
                breakdown=breakdown
            )

        # RESCAN condition
        if composite_score >= thresh.rescan_threshold_lower:
            hint = l3.user_hint or "Tilt the note slowly under good lighting and hold it inside the guide frame"
            return VerificationDecision(
                decision="RESCAN",
                score=round(composite_score, 4),
                reason_code="UNCERTAIN_CONFIDENCE_RESCAN_REQUIRED",
                human_reason="Feature confidence was below acceptable threshold for definitive verification",
                user_hint=hint,
                voucher=None,
                breakdown=breakdown
            )

        # Otherwise REJECT
        return VerificationDecision(
            decision="REJECT",
            score=round(composite_score, 4),
            reason_code="VERIFICATION_FAILED",
            human_reason="Banknote failed security verification standards",
            user_hint="Ensure the banknote is clean, undamaged, and supported by MONY",
            voucher=None,
            breakdown=breakdown
        )

    def _create_signed_voucher(
        self,
        user_address: str,
        amount_wei: int,
        amount_mon: float,
        denomination_inr: int,
        note_hash: str
    ) -> SignedVoucher:
        self._nonce_counter += 1
        nonce = self._nonce_counter
        expiry = int(time.time()) + 300  # 5 minutes validity

        eip712_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "Voucher": [
                    {"name": "user", "type": "address"},
                    {"name": "amountWei", "type": "uint256"},
                    {"name": "noteHash", "type": "bytes32"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "expiry", "type": "uint256"}
                ]
            },
            "primaryType": "Voucher",
            "domain": {
                "name": "MonyTreasury",
                "version": "1",
                "chainId": self.chain_id,
                "verifyingContract": self.treasury_address
            },
            "message": {
                "user": user_address,
                "amountWei": amount_wei,
                "noteHash": bytes.fromhex(note_hash[2:] if note_hash.startswith("0x") else note_hash),
                "nonce": nonce,
                "expiry": expiry
            }
        }

        signable = encode_typed_data(full_message=eip712_data)
        signed = Account.sign_message(signable, private_key=self.verifier_key)
        sig_hex = signed.signature.hex()
        if not sig_hex.startswith("0x"):
            sig_hex = "0x" + sig_hex

        return SignedVoucher(
            user=user_address,
            amount_wei=str(amount_wei),
            amount_mon=amount_mon,
            denomination_inr=denomination_inr,
            note_hash=note_hash,
            nonce=nonce,
            expiry=expiry,
            signature=sig_hex
        )
