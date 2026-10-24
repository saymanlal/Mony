import hmac
import hashlib
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import numpy as np
from .config import EngineConfig, DEFAULT_CONFIG

class SensorSample(BaseModel):
    timestamp_ms: int
    x: float
    y: float
    z: float

class CaptureMetadata(BaseModel):
    nonce: str
    issued_at_ms: int
    expiry_ms: int
    hmac_signature: str
    frame_timestamps_ms: List[int]
    accelerometer_samples: List[SensorSample]
    gyroscope_samples: List[SensorSample]

class Layer0Result(BaseModel):
    passed: bool
    score: float
    reason_code: str
    details: Dict[str, Any]

class Layer0CaptureValidator:
    def __init__(self, secret_key: str, config: Optional[EngineConfig] = None):
        self.secret_key = secret_key.encode("utf-8")
        self.config = config or DEFAULT_CONFIG
        self.used_nonces = set()

    def create_challenge(self, ttl_seconds: int = 120) -> Dict[str, Any]:
        now_ms = int(time.time() * 1000)
        expiry_ms = now_ms + (ttl_seconds * 1000)
        nonce = hashlib.sha256(f"{now_ms}:{time.monotonic_ns()}".encode("utf-8")).hexdigest()
        
        message = f"{nonce}:{now_ms}:{expiry_ms}".encode("utf-8")
        signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
        
        return {
            "nonce": nonce,
            "issued_at_ms": now_ms,
            "expiry_ms": expiry_ms,
            "hmac_signature": signature
        }

    def validate_capture(self, metadata: CaptureMetadata) -> Layer0Result:
        now_ms = int(time.time() * 1000)
        
        # 1. Nonce single-use check
        if metadata.nonce in self.used_nonces:
            return Layer0Result(
                passed=False,
                score=0.0,
                reason_code="NONCE_REUSED",
                details={"message": "Capture challenge nonce has already been used"}
            )
            
        # 2. HMAC signature verification
        expected_msg = f"{metadata.nonce}:{metadata.issued_at_ms}:{metadata.expiry_ms}".encode("utf-8")
        expected_sig = hmac.new(self.secret_key, expected_msg, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, metadata.hmac_signature):
            return Layer0Result(
                passed=False,
                score=0.0,
                reason_code="INVALID_CHALLENGE_HMAC",
                details={"message": "Challenge HMAC signature verification failed"}
            )
            
        # 3. Expiry check
        if now_ms > metadata.expiry_ms:
            return Layer0Result(
                passed=False,
                score=0.0,
                reason_code="CHALLENGE_EXPIRED",
                details={"message": "Capture challenge expired", "now_ms": now_ms, "expiry_ms": metadata.expiry_ms}
            )
            
        # 4. Frame count check
        frame_count = len(metadata.frame_timestamps_ms)
        thresh = self.config.thresholds
        if frame_count < thresh.min_frames:
            return Layer0Result(
                passed=False,
                score=0.1,
                reason_code="TOO_FEW_FRAMES",
                details={"frame_count": frame_count, "min_required": thresh.min_frames}
            )
        if frame_count > thresh.max_frames:
            return Layer0Result(
                passed=False,
                score=0.2,
                reason_code="TOO_MANY_FRAMES",
                details={"frame_count": frame_count, "max_allowed": thresh.max_frames}
            )
            
        # 5. Timing plausibility
        timestamps = sorted(metadata.frame_timestamps_ms)
        duration_s = (timestamps[-1] - timestamps[0]) / 1000.0
        if duration_s < thresh.min_duration_seconds:
            return Layer0Result(
                passed=False,
                score=0.3,
                reason_code="CAPTURE_TOO_FAST",
                details={"duration_s": duration_s, "min_required_s": thresh.min_duration_seconds}
            )
            
        # Check frame intervals
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        if any(dt < 40 for dt in intervals):  # implausibly high frame rate (> 25 fps burst)
            return Layer0Result(
                passed=False,
                score=0.2,
                reason_code="IMPLAUSIBLE_FRAME_TIMING",
                details={"min_interval_ms": min(intervals)}
            )
            
        # 6. Device motion verification (gyroscope and accelerometer)
        if len(metadata.gyroscope_samples) < 5 or len(metadata.accelerometer_samples) < 5:
            return Layer0Result(
                passed=False,
                score=0.1,
                reason_code="INSUFFICIENT_SENSOR_DATA",
                details={"gyro_count": len(metadata.gyroscope_samples), "accel_count": len(metadata.accelerometer_samples)}
            )
            
        # Gyro motion variance
        gyro_norms = [np.sqrt(s.x**2 + s.y**2 + s.z**2) for s in metadata.gyroscope_samples]
        gyro_std = float(np.std(gyro_norms))
        
        # Accelerometer motion variance
        accel_norms = [np.sqrt(s.x**2 + s.y**2 + s.z**2) for s in metadata.accelerometer_samples]
        accel_std = float(np.std(accel_norms))
        
        if gyro_std < thresh.min_device_motion_gyro_std and accel_std < thresh.min_device_motion_accel_std:
            return Layer0Result(
                passed=False,
                score=0.25,
                reason_code="NO_DEVICE_MOTION",
                details={"gyro_std": gyro_std, "accel_std": accel_std, "message": "Static camera feed or lack of natural tilt detected"}
            )
            
        # Mark nonce as consumed
        self.used_nonces.add(metadata.nonce)
        
        return Layer0Result(
            passed=True,
            score=1.0,
            reason_code="CAPTURE_INTEGRITY_VERIFIED",
            details={
                "frame_count": frame_count,
                "duration_s": duration_s,
                "gyro_std": gyro_std,
                "accel_std": accel_std
            }
        )
