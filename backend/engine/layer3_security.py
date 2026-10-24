import cv2
import json
import os
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .config import EngineConfig, DEFAULT_CONFIG

class Layer3Result(BaseModel):
    passed: bool
    score: float
    reason_code: str
    user_hint: Optional[str]
    details: Dict[str, Any]

class Layer3SecurityVerifier:
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.profiles = self._load_profiles()

    def _load_profiles(self) -> Dict[str, Any]:
        path = self.config.profiles_path
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("denominations", {})
        return {}

    def verify_features(
        self,
        rectified_frames: List[np.ndarray],
        denomination: int
    ) -> Layer3Result:
        if not rectified_frames:
            return Layer3Result(
                passed=False,
                score=0.0,
                reason_code="NO_RECTIFIED_FRAMES",
                user_hint="Hold the note steady in the frame",
                details={}
            )

        profile = self.profiles.get(str(denomination), {})
        best_frame = rectified_frames[len(rectified_frames) // 2]
        h, w = best_frame.shape[:2]

        # 1. Security Thread Presence and Position
        thread_score = self._check_security_thread(best_frame, profile)

        # 2. Color Shift across tilted frames
        color_shift_score, hue_delta = self._check_color_shift(rectified_frames, profile)

        # 3. Watermark Window Contrast
        watermark_score = self._check_watermark_region(best_frame, profile)

        # 4. Microtext Sharpness
        microtext_score = self._check_microtext(best_frame)

        # 5. Portrait Region Match Score
        portrait_score = self._check_portrait_region(best_frame, profile)

        # 6. See-through Register Check
        register_score = self._check_see_through_register(best_frame)

        # Check lighting conditions for hints
        if len(best_frame.shape) == 3 and best_frame.shape[2] == 3:
            gray = cv2.cvtColor(best_frame, cv2.COLOR_BGR2GRAY)
        elif len(best_frame.shape) == 3 and best_frame.shape[2] == 1:
            gray = best_frame[:, :, 0]
        else:
            gray = best_frame
        mean_brightness = float(np.mean(gray))
        glare_ratio = float(np.count_nonzero(gray > 240) / gray.size)

        user_hint = None
        if mean_brightness < 70.0:
            user_hint = "Provide more ambient lighting on the note"
        elif glare_ratio > 0.15:
            user_hint = "Reduce direct glare or reflections on the note"
        elif profile.get("security_thread", {}).get("color_shift", False) and hue_delta < 8.0:
            user_hint = "Tilt the note slowly to catch the color-shifting thread"
        elif portrait_score < 0.40:
            user_hint = "Ensure the front side of the note with Mahatma Gandhi portrait is visible"

        thresh = self.config.thresholds
        weights = [0.25, 0.20, 0.15, 0.15, 0.15, 0.10]
        scores = [
            thread_score,
            color_shift_score,
            watermark_score,
            microtext_score,
            portrait_score,
            register_score
        ]
        composite_score = float(np.average(scores, weights=weights))

        passed = composite_score >= thresh.layer3_min_score
        reason_code = "SECURITY_FEATURES_AUTHENTICATED" if passed else "SECURITY_FEATURE_ANOMALY"

        return Layer3Result(
            passed=passed,
            score=round(composite_score, 4),
            reason_code=reason_code,
            user_hint=user_hint,
            details={
                "security_thread_score": round(thread_score, 4),
                "color_shift_score": round(color_shift_score, 4),
                "hue_delta": round(hue_delta, 2),
                "watermark_score": round(watermark_score, 4),
                "microtext_score": round(microtext_score, 4),
                "portrait_score": round(portrait_score, 4),
                "register_score": round(register_score, 4),
                "mean_brightness": round(mean_brightness, 2),
                "glare_ratio": round(glare_ratio, 4)
            }
        )

    def _check_security_thread(self, frame: np.ndarray, profile: Dict[str, Any]) -> float:
        thread_info = profile.get("security_thread", {})
        if not thread_info.get("present", True):
            return 1.0

        h, w = frame.shape[:2]
        pos_ratio = thread_info.get("position_x_ratio", 0.44)
        x_center = int(w * pos_ratio)
        x_start = max(0, x_center - int(w * 0.02))
        x_end = min(w, x_center + int(w * 0.02))

        thread_strip = frame[:, x_start:x_end]
        if thread_strip.size == 0:
            return 0.0

        gray_strip = cv2.cvtColor(thread_strip, cv2.COLOR_BGR2GRAY) if len(thread_strip.shape) == 3 else thread_strip
        # Security thread presents a prominent vertical gradient contrast against adjacent paper
        col_means = np.mean(gray_strip, axis=0)
        overall_mean = np.mean(gray_strip)
        contrast = float(np.std(col_means) / (overall_mean + 1e-5))

        # Check for windowed segments (periodic vertical variance)
        vert_profile = np.mean(gray_strip, axis=1)
        vert_variance = float(np.std(vert_profile))

        score = float(np.clip((contrast * 3.0) + (vert_variance / 40.0), 0.0, 1.0))
        return score

    def _check_color_shift(self, frames: List[np.ndarray], profile: Dict[str, Any]) -> (float, float):
        thread_info = profile.get("security_thread", {})
        has_shift = thread_info.get("color_shift", False)
        if not has_shift or len(frames) < 2:
            return 1.0, 0.0

        h, w = frames[0].shape[:2]
        pos_ratio = thread_info.get("position_x_ratio", 0.44)
        x_center = int(w * pos_ratio)
        x_start = max(0, x_center - 15)
        x_end = min(w, x_center + 15)

        hues = []
        for f in frames:
            strip = f[int(h*0.3):int(h*0.7), x_start:x_end]
            if strip.size > 0:
                if len(strip.shape) == 3:
                    hsv = cv2.cvtColor(strip, cv2.COLOR_BGR2HSV)
                    mean_h = np.mean(hsv[:, :, 0])
                else:
                    mean_h = np.mean(strip)
                hues.append(mean_h)

        if not hues:
            return 0.5, 0.0

        hue_delta = float(max(hues) - min(hues))
        score = float(np.clip(hue_delta / self.config.thresholds.min_thread_color_shift, 0.0, 1.0))
        return score, hue_delta

    def _check_watermark_region(self, frame: np.ndarray, profile: Dict[str, Any]) -> float:
        h, w = frame.shape[:2]
        wm_info = profile.get("watermark_window", {})
        x1 = int(w * wm_info.get("x_min_ratio", 0.05))
        x2 = int(w * wm_info.get("x_max_ratio", 0.30))
        y1 = int(h * wm_info.get("y_min_ratio", 0.15))
        y2 = int(h * wm_info.get("y_max_ratio", 0.85))

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return 0.0

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
        mean_b = float(np.mean(gray))
        std_b = float(np.std(gray))

        contrast_score = float(np.clip(std_b / 30.0, 0.0, 1.0))
        return contrast_score

    def _check_microtext(self, frame: np.ndarray) -> float:
        h, w = frame.shape[:2]
        roi = frame[int(h*0.05):int(h*0.25), int(w*0.35):int(w*0.65)]
        if roi.size == 0:
            return 0.5

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge_energy = float(np.mean(np.sqrt(sobel_x**2 + sobel_y**2)))

        score = float(np.clip(edge_energy / 40.0, 0.0, 1.0))
        return score

    def _check_portrait_region(self, frame: np.ndarray, profile: Dict[str, Any]) -> float:
        h, w = frame.shape[:2]
        p_info = profile.get("portrait_region", {})
        x1 = int(w * p_info.get("x_min_ratio", 0.48))
        x2 = int(w * p_info.get("x_max_ratio", 0.78))
        y1 = int(h * p_info.get("y_min_ratio", 0.15))
        y2 = int(h * p_info.get("y_max_ratio", 0.85))

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return 0.0

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_norm = hist / hist.sum()
        entropy = float(-np.sum([p * np.log2(p + 1e-7) for p in hist_norm.ravel() if p > 0]))

        score = float(np.clip(entropy / 7.5, 0.0, 1.0))
        return score

    def _check_see_through_register(self, frame: np.ndarray) -> float:
        h, w = frame.shape[:2]
        roi = frame[int(h*0.35):int(h*0.65), 0:int(w*0.12)]
        if roi.size == 0:
            return 0.5

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        score = float(np.clip(np.var(lap) / 80.0, 0.0, 1.0))
        return score
