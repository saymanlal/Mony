import os
from pydantic import BaseModel, Field
from typing import Dict, List

class VerificationThresholds(BaseModel):
    min_frames: int = 6
    max_frames: int = 15
    min_duration_seconds: float = 2.0
    min_device_motion_gyro_std: float = 0.05
    min_device_motion_accel_std: float = 0.08
    
    # Layer 1 thresholds (0.0 to 1.0, higher means more genuine/paper-like)
    layer1_min_score: float = 0.60
    max_moire_fft_peak_ratio: float = 0.32
    min_paper_fibre_variance: float = 2.0
    max_halftone_dot_score: float = 0.50
    max_screen_bezel_confidence: float = 0.35
    min_specular_variance_across_tilt: float = 1.0
    
    # Layer 2 thresholds
    layer2_min_score: float = 0.60
    max_aspect_ratio_error: float = 0.09
    min_orb_match_count: int = 14
    min_color_histogram_similarity: float = 0.60
    
    # Layer 3 thresholds
    layer3_min_score: float = 0.60
    min_security_thread_score: float = 0.50
    min_thread_color_shift: float = 10.0
    min_watermark_contrast_score: float = 0.45
    min_microtext_sharpness_score: float = 0.45
    min_portrait_template_score: float = 0.50
    
    # Layer 4 thresholds
    layer4_min_score: float = 0.60
    max_phash_hamming_distance_duplicate: int = 6
    
    # Overall decision
    overall_pass_threshold: float = 0.65
    rescan_threshold_lower: float = 0.50
    
    # Layer weights for combined score
    weight_layer1: float = 0.35
    weight_layer2: float = 0.25
    weight_layer3: float = 0.25
    weight_layer4: float = 0.15

class EngineConfig(BaseModel):
    server_salt: str = Field(default_factory=lambda: os.getenv("SERVER_SALT", "MONY_PRODUCTION_SALT_SECRET_SALT_2026"))
    supported_denominations: List[int] = [10, 20, 50, 100, 200, 500]
    profiles_path: str = Field(
        default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiles", "inr.json")
    )
    thresholds: VerificationThresholds = VerificationThresholds()

DEFAULT_CONFIG = EngineConfig()
