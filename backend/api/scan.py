"""
Scan and banknote verification endpoints for MONY.
"""

from __future__ import annotations

import json
import logging
import time
from typing import List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

import db
from engine.layer0_capture import CaptureMetadata
import main

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["scan"])


class ChallengeResponse(BaseModel):
    nonce: str
    issued_at_ms: int
    expiry_ms: int
    hmac_signature: str
    session_id: str


@router.post("/challenge", response_model=ChallengeResponse)
async def create_challenge() -> ChallengeResponse:
    if main.banknote_verifier is None:
        raise HTTPException(status_code=503, detail="Verification engine not initialized")
    
    challenge = main.banknote_verifier.layer0.create_challenge(ttl_seconds=120)
    session_id = f"sess_{challenge['nonce'][:16]}"
    return ChallengeResponse(
        nonce=challenge["nonce"],
        issued_at_ms=challenge["issued_at_ms"],
        expiry_ms=challenge["expiry_ms"],
        hmac_signature=challenge["hmac_signature"],
        session_id=session_id,
    )


@router.post("/verify")
async def verify_scan(
    frames: List[UploadFile] = File(...),
    metadata: str = Form(...),
    user_address: str = Form(...),
):
    if main.banknote_verifier is None:
        raise HTTPException(status_code=503, detail="Verification engine not initialized")

    try:
        meta_dict = json.loads(metadata)
        capture_meta = CaptureMetadata(**meta_dict)
    except Exception as e:
        logger.error(f"Failed to parse scan metadata: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid capture metadata format: {str(e)}")

    if len(frames) < 6:
        raise HTTPException(status_code=400, detail="At least 6 frames required for 3D tilt verification")

    # Read uploaded image frames into numpy arrays
    loaded_frames: List[np.ndarray] = []
    for f in frames:
        contents = await f.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            loaded_frames.append(img)

    if len(loaded_frames) < 6:
        raise HTTPException(status_code=400, detail="Failed to decode sufficient valid image frames")

    # Fetch existing note hashes and perceptual hashes from DB
    existing_hashes = set()
    existing_phashes = []
    try:
        records = await db.get_all_redeemed_note_hashes()
        for r in records:
            existing_hashes.add(r["note_hash"])
            if r.get("phash"):
                existing_phashes.append(r["phash"])
    except Exception as e:
        logger.warning(f"Could not load historical hashes from database: {e}")

    # Estimate preliminary quote
    inr_per_mon = main.settings.demo_inr_per_mon
    if main.rate_service is not None:
        try:
            rate_data = await main.rate_service.get_inr_per_mon()
            inr_per_mon = rate_data.get("inr_per_mon", main.settings.demo_inr_per_mon)
        except Exception:
            pass

    # Default estimation basis
    denom_est = 100
    amount_mon = round(denom_est / inr_per_mon, 6)
    amount_wei = int(amount_mon * 10**18)

    decision = main.banknote_verifier.verify_scan(
        frames=loaded_frames,
        metadata=capture_meta,
        user_address=user_address,
        amount_wei=amount_wei,
        amount_mon=amount_mon,
        existing_note_hashes=existing_hashes,
        existing_phashes=existing_phashes,
    )

    # Persist scan result to DB
    try:
        await db.record_scan(
            user_address=user_address,
            decision=decision.decision,
            reason_code=decision.reason_code,
            score=decision.score,
            voucher_data=decision.voucher.model_dump() if decision.voucher else None,
            breakdown=decision.breakdown,
        )
    except Exception as e:
        logger.error(f"Failed to record scan in database: {e}")

    return decision.model_dump()
