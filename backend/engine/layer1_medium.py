import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .config import EngineConfig, DEFAULT_CONFIG

class MediumCheckDetails(BaseModel):
    fft_moire_peak_ratio: float
    specular_tilt_variance: float
    screen_bezel_detected: bool
    halftone_dot_score: float
    paper_fibre_variance: float
    intaglio_sharpness: float

class Layer1Result(BaseModel):
    passed: bool
    score: float
    reason_code: str
    details: Dict[str, Any]

def _to_gray(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        if img.shape[2] == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif img.shape[2] == 1:
            return img[:, :, 0]
    return img

class Layer1MediumDetector:
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or DEFAULT_CONFIG

    def analyze_frames(self, frames: List[np.ndarray]) -> Layer1Result:
        if not frames:
            return Layer1Result(
                passed=False,
                score=0.0,
                reason_code="NO_FRAMES_PROVIDED",
                details={}
            )
            
        thresh = self.config.thresholds
        primary_frame = frames[len(frames) // 2]
        gray = _to_gray(primary_frame)
        h, w = gray.shape

        # 1. FFT Moire and Pixel Grid Analysis
        fft_peak_ratio = self._detect_moire_fft(gray)
        is_moire_screen = fft_peak_ratio > thresh.max_moire_fft_peak_ratio

        # 2. Specular Glare and Emissive Behavior across tilted frames
        specular_tilt_variance = self._analyze_specular_tilt_variance(frames)
        is_flat_emissive = specular_tilt_variance < thresh.min_specular_variance_across_tilt

        # 3. Screen Bezel Detection
        bezel_detected, bezel_conf = self._detect_screen_bezel(primary_frame)

        # 4. Halftone Dot Pattern Analysis (Prints and Photocopies)
        halftone_score = self._detect_halftone_patterns(gray)
        is_halftone_print = halftone_score > thresh.max_halftone_dot_score

        # 5. Paper Fibre Texture Analysis
        fibre_variance = self._analyze_paper_fibre(gray)
        lacks_fibre = fibre_variance < thresh.min_paper_fibre_variance

        # 6. Intaglio Edge Sharpness
        intaglio_sharpness = self._measure_intaglio_sharpness(gray)

        # Compute individual sub-scores (0.0 to 1.0, where 1.0 is genuine physical banknote)
        score_moire = max(0.0, 1.0 - (fft_peak_ratio / (thresh.max_moire_fft_peak_ratio * 1.8)))
        score_specular = min(1.0, specular_tilt_variance / (thresh.min_specular_variance_across_tilt * 2.0))
        score_bezel = 1.0 - bezel_conf
        score_halftone = max(0.0, 1.0 - (halftone_score / (thresh.max_halftone_dot_score * 1.8)))
        score_fibre = min(1.0, fibre_variance / (thresh.min_paper_fibre_variance * 2.0))
        score_intaglio = min(1.0, intaglio_sharpness / 120.0)

        weights = [0.25, 0.20, 0.15, 0.15, 0.15, 0.10]
        sub_scores = [score_moire, score_specular, score_bezel, score_halftone, score_fibre, score_intaglio]
        aggregate_score = float(np.average(sub_scores, weights=weights))

        # Check for immediate negative tripwires
        if is_moire_screen:
            return Layer1Result(
                passed=False,
                score=min(aggregate_score, 0.35),
                reason_code="SCREEN_MOIRE_GRID_DETECTED",
                details={
                    "fft_peak_ratio": fft_peak_ratio,
                    "threshold": thresh.max_moire_fft_peak_ratio,
                    "message": "Digital display pixel grid or moire interference detected"
                }
            )

        if bezel_detected and bezel_conf > thresh.max_screen_bezel_confidence:
            return Layer1Result(
                passed=False,
                score=min(aggregate_score, 0.30),
                reason_code="SCREEN_BEZEL_DETECTED",
                details={
                    "bezel_confidence": bezel_conf,
                    "threshold": thresh.max_screen_bezel_confidence,
                    "message": "Device bezel or monitor frame boundary detected"
                }
            )

        if is_halftone_print:
            return Layer1Result(
                passed=False,
                score=min(aggregate_score, 0.40),
                reason_code="HALFTONE_PRINT_PATTERN_DETECTED",
                details={
                    "halftone_score": halftone_score,
                    "threshold": thresh.max_halftone_dot_score,
                    "message": "Printer screening or photocopy halftone dot structure detected"
                }
            )

        if is_flat_emissive and lacks_fibre:
            return Layer1Result(
                passed=False,
                score=min(aggregate_score, 0.45),
                reason_code="EMISSIVE_SCREEN_TEXTURE_ABSENT",
                details={
                    "specular_tilt_variance": specular_tilt_variance,
                    "fibre_variance": fibre_variance,
                    "message": "Lack of physical paper substrate and dynamic specular reflections"
                }
            )

        passed = aggregate_score >= thresh.layer1_min_score
        reason_code = "PHYSICAL_MEDIUM_VERIFIED" if passed else "MEDIUM_INTEGRITY_UNCERTAIN"

        return Layer1Result(
            passed=passed,
            score=round(aggregate_score, 4),
            reason_code=reason_code,
            details={
                "fft_peak_ratio": round(fft_peak_ratio, 4),
                "specular_tilt_variance": round(specular_tilt_variance, 4),
                "bezel_confidence": round(bezel_conf, 4),
                "halftone_score": round(halftone_score, 4),
                "fibre_variance": round(fibre_variance, 4),
                "intaglio_sharpness": round(intaglio_sharpness, 4),
                "sub_scores": [round(s, 4) for s in sub_scores]
            }
        )

    def _detect_moire_fft(self, gray: np.ndarray) -> float:
        # Resize to standard analysis patch for scale invariance
        patch = cv2.resize(gray, (512, 512))
        f = np.fft.fft2(patch)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1.0)
        
        # Zero out center DC and low frequency radius
        cy, cx = 256, 256
        y, x = np.ogrid[:512, :512]
        mask_low = ((x - cx)**2 + (y - cy)**2) <= (32**2)
        magnitude_spectrum[mask_low] = 0.0

        # High frequency energy analysis
        median_energy = np.median(magnitude_spectrum)
        max_peaks = np.sort(magnitude_spectrum.ravel())[-50:]
        peak_ratio = float((np.mean(max_peaks) - median_energy) / (median_energy + 1e-6))
        return float(np.clip(peak_ratio / 10.0, 0.0, 1.0))

    def _analyze_specular_tilt_variance(self, frames: List[np.ndarray]) -> float:
        if len(frames) < 2:
            return 0.0
            
        frame_means = []
        frame_stds = []
        for f in frames:
            g = _to_gray(f)
            # Sample highlight brightness across note region
            h, w = g.shape
            roi = g[int(h*0.25):int(h*0.75), int(w*0.25):int(w*0.75)]
            frame_means.append(np.mean(roi))
            frame_stds.append(np.std(roi))

        variance_across_tilt = float(np.std(frame_means) + np.std(frame_stds))
        return variance_across_tilt

    def _detect_screen_bezel(self, bgr: np.ndarray) -> (bool, float):
        gray = _to_gray(bgr)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        h, w = gray.shape
        total_area = h * w
        
        outer_boxes = 0
        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) == 4:
                area = cv2.contourArea(approx)
                if area > 0.40 * total_area and area < 0.98 * total_area:
                    outer_boxes += 1
                    
        # If multiple concentric rectangular borders detected around the note, strong sign of phone/monitor bezel
        if outer_boxes >= 2:
            return True, 0.85
        elif outer_boxes == 1:
            return False, 0.30
        return False, 0.05

    def _detect_halftone_patterns(self, gray: np.ndarray) -> float:
        # Standard prints have periodic CMYK halftone screening in mid-tone areas
        h, w = gray.shape
        patch = gray[h//4:3*h//4, w//4:3*w//4].astype(np.float32)
        if patch.size == 0:
            return 0.0
            
        blurred = cv2.GaussianBlur(patch, (9, 9), 0)
        res = patch - blurred
        
        # Check autocorrelation at print screening periodicity (lag 8 pixels)
        shifted_x = np.roll(res, 8, axis=1)
        corr_x = np.corrcoef(res.ravel(), shifted_x.ravel())[0, 1]
        score = float(np.clip(corr_x, 0.0, 1.0)) if not np.isnan(corr_x) else 0.0
        return score

    def _analyze_paper_fibre(self, gray: np.ndarray) -> float:
        # Measure micro-roughness in note region (center/margins)
        h, w = gray.shape
        roi = gray[int(h*0.35):int(h*0.65), int(w*0.30):int(w*0.70)]
        if roi.size == 0:
            return 0.0
            
        blurred = cv2.GaussianBlur(roi, (3, 3), 0)
        residual = cv2.absdiff(roi, blurred)
        fibre_variance = float(np.var(residual))
        return fibre_variance

    def _measure_intaglio_sharpness(self, gray: np.ndarray) -> float:
        # Sharp intaglio lines yield high Laplacian variance in portrait/text regions
        h, w = gray.shape
        detail_roi = gray[int(h*0.2):int(h*0.8), int(w*0.4):int(w*0.9)]
        if detail_roi.size == 0:
            return 0.0
            
        lap = cv2.Laplacian(detail_roi, cv2.CV_64F)
        sharpness = float(np.var(lap))
        return sharpness
