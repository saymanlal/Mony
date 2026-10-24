import os
from typing import List, Dict, Any, Optional
import numpy as np
from .config import EngineConfig, DEFAULT_CONFIG
from .layer0_capture import Layer0CaptureValidator, CaptureMetadata
from .layer1_medium import Layer1MediumDetector
from .layer2_geometry import Layer2GeometryClassifier
from .layer3_security import Layer3SecurityVerifier
from .layer4_serial import Layer4SerialDuplicateEngine
from .layer5_decision import Layer5DecisionEngine, VerificationDecision

class BanknoteVerifier:
    def __init__(
        self,
        verifier_private_key: str,
        treasury_address: str,
        challenge_secret: str,
        chain_id: int = 10143,
        config: Optional[EngineConfig] = None
    ):
        self.config = config or DEFAULT_CONFIG
        self.layer0 = Layer0CaptureValidator(secret_key=challenge_secret, config=self.config)
        self.layer1 = Layer1MediumDetector(config=self.config)
        self.layer2 = Layer2GeometryClassifier(config=self.config)
        self.layer3 = Layer3SecurityVerifier(config=self.config)
        self.layer4 = Layer4SerialDuplicateEngine(config=self.config)
        self.layer5 = Layer5DecisionEngine(
            verifier_private_key=verifier_private_key,
            treasury_address=treasury_address,
            chain_id=chain_id,
            config=self.config
        )

    def verify_scan(
        self,
        frames: List[np.ndarray],
        metadata: CaptureMetadata,
        user_address: str,
        amount_wei: int,
        amount_mon: float,
        existing_note_hashes: Optional[set] = None,
        existing_phashes: Optional[List[str]] = None
    ) -> VerificationDecision:
        # Layer 0: Capture Integrity
        l0_result = self.layer0.validate_capture(metadata)
        if not l0_result.passed:
            return self.layer5.evaluate(
                l0=l0_result,
                l1=None,
                l2=None,
                l3=None,
                l4=None,
                user_address=user_address,
                amount_wei=amount_wei,
                amount_mon=amount_mon,
                denomination_inr=0
            )

        # Layer 1: Medium Detection (Screen / Print / Fibre / Halftone)
        l1_result = self.layer1.analyze_frames(frames)

        # Layer 2: Geometry, Rectification, and Denomination consensus
        primary_frame = frames[len(frames) // 2]
        l2_result, rectified = self.layer2.process(primary_frame)

        if rectified is None:
            # Note contour not detected
            return self.layer5.evaluate(
                l0=l0_result,
                l1=l1_result,
                l2=l2_result,
                l3=None,
                l4=None,
                user_address=user_address,
                amount_wei=amount_wei,
                amount_mon=amount_mon,
                denomination_inr=0
            )

        denomination = l2_result.denomination or 100

        # Rectify all frames for multi-frame tilt and color-shift analysis
        rectified_frames = []
        for f in frames:
            rect_img, _, _ = self.layer2._locate_and_rectify(f)
            if rect_img is not None:
                rectified_frames.append(rect_img)
            else:
                rectified_frames.append(rectified)

        # Layer 3: Security Features
        l3_result = self.layer3.verify_features(rectified_frames, denomination)

        # Layer 4: Serial and Duplicate Prevention
        l4_result = self.layer4.process_serial_and_hash(
            rectified_frame=rectified,
            denomination=denomination,
            existing_note_hashes=existing_note_hashes,
            existing_phashes=existing_phashes
        )

        # Layer 5: Decision Aggregation and Signed Voucher
        decision = self.layer5.evaluate(
            l0=l0_result,
            l1=l1_result,
            l2=l2_result,
            l3=l3_result,
            l4=l4_result,
            user_address=user_address,
            amount_wei=amount_wei,
            amount_mon=amount_mon,
            denomination_inr=denomination
        )

        return decision
