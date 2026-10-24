import cv2
import json
import os
import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel
from .config import EngineConfig, DEFAULT_CONFIG

class Layer2Result(BaseModel):
    passed: bool
    score: float
    denomination: Optional[int]
    aspect_ratio: float
    reason_code: str
    details: Dict[str, Any]

def _to_gray(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        if img.shape[2] == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif img.shape[2] == 1:
            return img[:, :, 0]
    return img

def _to_bgr(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 1:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img

class Layer2GeometryClassifier:
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.profiles = self._load_profiles()
        self.orb = cv2.ORB_create(nfeatures=1200)
        self.bf_matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        self.reference_descriptors: Dict[int, Any] = {}

    def _load_profiles(self) -> Dict[str, Any]:
        path = self.config.profiles_path
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("denominations", {})
        return {}

    def set_reference_templates(self, reference_templates: Dict[int, np.ndarray]):
        for denom, img in reference_templates.items():
            gray = _to_gray(img)
            kp, des = self.orb.detectAndCompute(gray, None)
            if des is not None:
                self.reference_descriptors[denom] = (kp, des)

    def process(self, frame: np.ndarray) -> Tuple[Layer2Result, Optional[np.ndarray]]:
        # 1. Locate and Rectify Note
        rectified, corners, aspect_ratio = self._locate_and_rectify(frame)
        if rectified is None:
            return Layer2Result(
                passed=False,
                score=0.1,
                denomination=None,
                aspect_ratio=0.0,
                reason_code="NOTE_CONTOUR_NOT_FOUND",
                details={"message": "Could not locate 4-corner banknote contour in frame"}
            ), None

        # 2. Color Classification via dominant hue best-fit
        color_scores = self._classify_by_color(rectified)
        best_color_denom = max(color_scores, key=color_scores.get)
        best_color_score = color_scores[best_color_denom]

        # 3. ORB Feature Matching (only used as tie-breaker when descriptors exist)
        has_orb_templates = len(self.reference_descriptors) > 0
        orb_scores = self._classify_by_orb(rectified) if has_orb_templates else {}
        best_orb_denom = max(orb_scores, key=orb_scores.get) if orb_scores else best_color_denom
        best_orb_matches = orb_scores.get(best_orb_denom, 0)

        # 4. Numeral Recognition
        numeral_denom, numeral_conf = self._classify_by_numeral(rectified)
        if numeral_denom is None:
            numeral_denom = best_color_denom

        # Choose candidate: prefer color+numeral consensus
        if best_color_denom == numeral_denom:
            candidate = best_color_denom
        elif has_orb_templates and best_orb_denom == best_color_denom:
            candidate = best_color_denom
        elif has_orb_templates and best_orb_denom == numeral_denom:
            candidate = numeral_denom
        else:
            candidate = best_color_denom

        profile = self.profiles.get(str(candidate), {})
        dim_info = profile.get("dimensions_mm", {})
        expected_ar = dim_info.get("aspect_ratio", 2.1)
        ar_tol = dim_info.get("aspect_ratio_tolerance", self.config.thresholds.max_aspect_ratio_error)

        ar_diff = abs(aspect_ratio - expected_ar)
        if ar_diff > ar_tol:
            return Layer2Result(
                passed=False,
                score=0.35,
                denomination=candidate,
                aspect_ratio=round(aspect_ratio, 3),
                reason_code="ASPECT_RATIO_MISMATCH",
                details={
                    "measured_aspect_ratio": round(aspect_ratio, 3),
                    "expected_aspect_ratio": expected_ar,
                    "tolerance": ar_tol
                }
            ), rectified

        # Agreement check
        color_numeral_agree = (best_color_denom == numeral_denom)

        # Calculate combined score
        score_ar = max(0.0, 1.0 - (ar_diff / ar_tol))
        score_color = min(1.0, best_color_score)
        score_numeral = numeral_conf

        if has_orb_templates and best_orb_matches > 0:
            score_orb = min(1.0, best_orb_matches / 25.0)
            combined_score = float(0.25 * score_ar + 0.30 * score_color + 0.25 * score_orb + 0.20 * score_numeral)
        else:
            # No ORB templates: weight color and numeral higher; give neutral orb contribution
            combined_score = float(0.25 * score_ar + 0.40 * score_color + 0.35 * score_numeral)

        # If color and numeral agree, accept even if ORB disagrees
        if color_numeral_agree:
            return Layer2Result(
                passed=True,
                score=round(min(combined_score, 1.0), 4),
                denomination=candidate,
                aspect_ratio=round(aspect_ratio, 3),
                reason_code="DENOMINATION_CLASSIFIED",
                details={
                    "color_denom": best_color_denom,
                    "numeral_denom": numeral_denom,
                    "orb_denom": best_orb_denom if has_orb_templates else None,
                    "orb_matches": best_orb_matches,
                    "color_score": round(score_color, 4),
                    "numeral_conf": round(numeral_conf, 4),
                    "ar_diff": round(ar_diff, 4)
                }
            ), rectified

        # ORB breaks tie when color and numeral disagree
        if has_orb_templates and (best_orb_denom == best_color_denom or best_orb_denom == numeral_denom):
            return Layer2Result(
                passed=True,
                score=round(min(combined_score * 0.90, 1.0), 4),
                denomination=best_orb_denom,
                aspect_ratio=round(aspect_ratio, 3),
                reason_code="DENOMINATION_CLASSIFIED_ORB_TIEBREAK",
                details={
                    "color_denom": best_color_denom,
                    "numeral_denom": numeral_denom,
                    "orb_denom": best_orb_denom,
                    "orb_matches": best_orb_matches,
                    "color_score": round(score_color, 4),
                    "numeral_conf": round(numeral_conf, 4),
                    "ar_diff": round(ar_diff, 4)
                }
            ), rectified

        # No agreement; low-confidence partial pass
        return Layer2Result(
            passed=combined_score >= 0.50,
            score=round(min(combined_score, 0.65), 4),
            denomination=candidate,
            aspect_ratio=round(aspect_ratio, 3),
            reason_code="DENOMINATION_CLASSIFICATION_CONFLICT" if combined_score < 0.50 else "DENOMINATION_LOW_CONFIDENCE",
            details={
                "color_denom": best_color_denom,
                "numeral_denom": numeral_denom,
                "orb_denom": best_orb_denom if has_orb_templates else None,
                "orb_matches": best_orb_matches,
                "color_score": round(score_color, 4),
                "numeral_conf": round(numeral_conf, 4),
                "ar_diff": round(ar_diff, 4)
            }
        ), rectified

    def _locate_and_rectify(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], float]:
        if frame is None or frame.size == 0:
            return None, None, 0.0

        # Safely handle unexpected shapes
        if len(frame.shape) == 2:
            bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif len(frame.shape) == 3 and frame.shape[2] == 1:
            bgr = cv2.cvtColor(frame[:, :, 0], cv2.COLOR_GRAY2BGR)
        elif len(frame.shape) == 3 and frame.shape[2] == 3:
            bgr = frame
        elif len(frame.shape) == 3 and frame.shape[2] == 4:
            bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        else:
            return None, None, 0.0

        h, w = bgr.shape[:2]
        frame_area = h * w

        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        best_quad = None
        max_area = 0.0

        # Try Canny edges with multiple thresholds for robustness
        for t_low, t_high in [(30, 100), (50, 150), (20, 80)]:
            edges = cv2.Canny(blurred, t_low, t_high)
            dilated = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 0.15 * frame_area:
                    continue
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.025 * peri, True)
                if len(approx) == 4 and area > max_area:
                    max_area = area
                    best_quad = approx.reshape(4, 2)

        # Fallback to saturation-based segmentation
        if best_quad is None:
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            sat = hsv[:, :, 1]
            _, sat_thresh = cv2.threshold(sat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(sat_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 0.15 * frame_area:
                    continue
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.025 * peri, True)
                if len(approx) == 4 and area > max_area:
                    max_area = area
                    best_quad = approx.reshape(4, 2)

        # Final fallback: use guide margins
        if best_quad is None:
            margin_x = int(w * 0.05)
            margin_y = int(h * 0.15)
            best_quad = np.array([
                [margin_x, margin_y],
                [w - margin_x, margin_y],
                [w - margin_x, h - margin_y],
                [margin_x, h - margin_y]
            ], dtype=np.float32)

        # Order points: top-left, top-right, bottom-right, bottom-left
        pts = np.array(best_quad, dtype=np.float32)
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)

        ordered = np.zeros((4, 2), dtype=np.float32)
        ordered[0] = pts[np.argmin(s)]        # Top-left
        ordered[2] = pts[np.argmax(s)]        # Bottom-right
        ordered[1] = pts[np.argmin(diff)]     # Top-right
        ordered[3] = pts[np.argmax(diff)]     # Bottom-left

        # Compute aspect ratio from the CONTOUR dimensions, not from output frame size
        width_top = float(np.linalg.norm(ordered[1] - ordered[0]))
        width_bot = float(np.linalg.norm(ordered[2] - ordered[3]))
        height_left = float(np.linalg.norm(ordered[3] - ordered[0]))
        height_right = float(np.linalg.norm(ordered[2] - ordered[1]))

        natural_w = (width_top + width_bot) / 2.0
        natural_h = (height_left + height_right) / 2.0

        if natural_h < 1.0 or natural_w < 1.0:
            return None, None, 0.0

        aspect_ratio = float(natural_w / natural_h)

        # Standardize target rectified dimensions to 1000 x int(1000 / aspect_ratio)
        target_w = 1000
        target_h = max(300, int(target_w / aspect_ratio))
        dst = np.array([
            [0, 0],
            [target_w - 1, 0],
            [target_w - 1, target_h - 1],
            [0, target_h - 1]
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(ordered, dst)
        rectified = cv2.warpPerspective(bgr, M, (target_w, target_h))

        return rectified, ordered, aspect_ratio

    def _classify_by_color(self, rectified: np.ndarray) -> Dict[int, float]:
        """
        Best-fit hue classification: compute the dominant hue of the rectified image
        and pick the denomination whose h_min/h_max center is closest.
        Measures pixels in range as primary score, plus proximity as secondary.
        """
        bgr = _to_bgr(rectified)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        h_channel = hsv[:, :, 0].astype(np.float32)
        s_channel = hsv[:, :, 1]
        v_channel = hsv[:, :, 2]

        # Restrict to saturated, bright pixels to exclude background
        valid_mask = (s_channel > 30) & (v_channel > 40)
        valid_hues = h_channel[valid_mask]

        scores = {}
        for denom_str, profile in self.profiles.items():
            denom = int(denom_str)
            h_range = profile.get("hsv_range", {})
            h_min = h_range.get("h_min", 0)
            h_max = h_range.get("h_max", 180)
            h_center = (h_min + h_max) / 2.0

            if valid_hues.size > 0:
                in_range = (valid_hues >= h_min) & (valid_hues <= h_max)
                ratio = float(np.count_nonzero(in_range) / valid_hues.size)
                median_hue = float(np.median(valid_hues))
                distance_score = max(0.0, 1.0 - abs(median_hue - h_center) / 90.0)
                scores[denom] = 0.70 * ratio + 0.30 * distance_score
            else:
                scores[denom] = 0.5

        if not scores:
            for d in [10, 20, 50, 100, 200, 500]:
                scores[d] = 0.5
        return scores

    def _classify_by_orb(self, rectified: np.ndarray) -> Dict[int, int]:
        gray = _to_gray(rectified)
        kp, des = self.orb.detectAndCompute(gray, None)
        scores = {}
        if des is None:
            return {d: 0 for d in self.config.supported_denominations}

        for denom, (ref_kp, ref_des) in self.reference_descriptors.items():
            matches = self.bf_matcher.knnMatch(des, ref_des, k=2)
            good = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.75 * n.distance:
                        good.append(m)
            scores[denom] = len(good)

        return scores

    def _classify_by_numeral(self, rectified: np.ndarray) -> Tuple[Optional[int], float]:
        h, w = rectified.shape[:2]
        numeral_rois = [
            rectified[int(h*0.75):h, int(w*0.70):w],
            rectified[0:int(h*0.35), 0:int(w*0.30)]
        ]

        text = ""
        for roi in numeral_rois:
            if roi.size == 0:
                continue
            gray_roi = _to_gray(roi)
            _, thresh = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            try:
                import pytesseract
                t = pytesseract.image_to_string(thresh, config="--psm 6 digits")
                text += " " + t
            except Exception:
                pass

        for denom in [500, 200, 100, 50, 20, 10]:
            if str(denom) in text:
                return denom, 0.95

        return None, 0.60
