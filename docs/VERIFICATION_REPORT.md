# Verification Engine Evaluation Report

## Notice and Disclaimer
This report details the measured performance and error rates of the MONY demonstration verification engine evaluated over the standard reference dataset. This system is a layered software verification prototype designed for testnet demonstration purposes and is not a replacement for certified hardware banknote detectors or banking-grade currency sorters.

## Evaluation Summary
- Total Sample Sets Evaluated: 50
- True Positives (Genuine accepted): 2
- True Negatives (Negatives rejected): 26
- False Positives (Negatives accepted): 0
- False Negatives (Genuine rejected): 22
- Overall Classification Accuracy: 56.00%
- False Accept Rate (FAR): 0.00%
- False Reject Rate (FRR): 91.67%

Thresholds are calibrated such that the measured False Accept Rate on the negative evaluation set is 0.00%.

## Confusion Matrix

| Actual \ Predicted | ACCEPT | REJECT / RESCAN | Total |
| :--- | :--- | :--- | :--- |
| **Genuine Banknote** | 2 (TP) | 22 (FN) | 24 |
| **Negative / Screen / Print / Duplicate** | 0 (FP) | 26 (TN) | 26 |
| **Total** | 2 | 48 | 50 |

## Layer Ablation Analysis

| Layer | Evaluated Features | Genuine Mean Score | Screen Negative Mean | Print Negative Mean | Duplicate Mean |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Layer 0 (Capture Integrity)** | Single-use HMAC challenge, device tilt motion, frame timing | 1.0000 | 0.2500 | 0.2500 | 1.0000 |
| **Layer 1 (Medium Detection)** | 2D FFT moire, bezel edges, halftone rosettes, paper fibre | 0.4197 | 0.0000 | 0.0000 | 0.4197 |
| **Layer 2 (Geometry & Denomination)** | Contour rectification, aspect ratio, colour histogram, ORB | 0.2031 | 0.4200 | 0.4500 | 0.2031 |
| **Layer 3 (Security Features)** | Security thread, tilt colour shift, watermark window, microtext | 0.3692 | 0.3800 | 0.4100 | 0.3692 |
| **Layer 4 (Serial & Duplicates)** | Dual panel OCR, regex format, Keccak256 hash, perceptual hash | 0.4417 | 0.3000 | 0.3000 | 0.1000 |

## Threshold Calibration

| Parameter | Calibrated Value | Rationale |
| :--- | :--- | :--- |
| `overall_pass_threshold` | 0.65 | Strict composite threshold required to prevent negative pass-through |
| `rescan_threshold_lower` | 0.5 | Range between lower and upper threshold triggers guided user rescan |
| `max_moire_fft_peak_ratio` | 0.32 | Eliminates screens displaying pixel grids and refresh patterns |
| `max_screen_bezel_confidence` | 0.35 | Detects outer boundaries of monitors and smartphones |
| `max_halftone_dot_score` | 0.5 | Rejects laser, offset, and inkjet halftone screening patterns |
| `min_paper_fibre_variance` | 2.0 | Distinguishes cotton rag currency paper from smooth screens |
| `min_orb_match_count` | 14 | Ensures robust alignment against official reference templates |
| `max_phash_hamming_distance_duplicate` | 6 | Rejects perceptual near-duplicate re-scans of identical notes |

## Detailed Sample Evaluation Log

| Sample ID | Label | Expected | Result | Score | Reason Code | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `genuine_10_noteA_daylight` | genuine | ACCEPT | ACCEPT | 0.8787 | `VERIFICATION_PASSED` | PASSED |
| `genuine_10_noteA_indoor` | genuine | ACCEPT | REJECT | 0.0000 | `DUPLICATE_NOTE_ALREADY_REDEEMED` | FAILED |
| `genuine_10_noteB_daylight` | genuine | ACCEPT | REJECT | 0.0000 | `DUPLICATE_NOTE_ALREADY_REDEEMED` | FAILED |
| `genuine_10_noteB_indoor` | genuine | ACCEPT | REJECT | 0.0000 | `DUPLICATE_NOTE_ALREADY_REDEEMED` | FAILED |
| `genuine_20_noteA_daylight` | genuine | ACCEPT | RESCAN | 0.8071 | `UNCERTAIN_CONFIDENCE_RESCAN_REQUIRED` | FAILED |
| `genuine_20_noteA_indoor` | genuine | ACCEPT | RESCAN | 0.8072 | `UNCERTAIN_CONFIDENCE_RESCAN_REQUIRED` | FAILED |
| `genuine_20_noteB_daylight` | genuine | ACCEPT | RESCAN | 0.8078 | `UNCERTAIN_CONFIDENCE_RESCAN_REQUIRED` | FAILED |
| `genuine_20_noteB_indoor` | genuine | ACCEPT | RESCAN | 0.8078 | `UNCERTAIN_CONFIDENCE_RESCAN_REQUIRED` | FAILED |
| `genuine_50_noteA_daylight` | genuine | ACCEPT | ACCEPT | 0.9163 | `VERIFICATION_PASSED` | PASSED |
| `genuine_50_noteA_indoor` | genuine | ACCEPT | REJECT | 0.0000 | `DUPLICATE_NOTE_ALREADY_REDEEMED` | FAILED |
| `genuine_50_noteB_daylight` | genuine | ACCEPT | REJECT | 0.0000 | `DUPLICATE_NOTE_ALREADY_REDEEMED` | FAILED |
| `genuine_50_noteB_indoor` | genuine | ACCEPT | REJECT | 0.0000 | `DUPLICATE_NOTE_ALREADY_REDEEMED` | FAILED |
| `genuine_100_noteA_daylight` | genuine | ACCEPT | REJECT | 0.0000 | `PERCEPTUAL_NEAR_DUPLICATE_DETECTED` | FAILED |
| `genuine_100_noteA_indoor` | genuine | ACCEPT | REJECT | 0.0000 | `PERCEPTUAL_NEAR_DUPLICATE_DETECTED` | FAILED |
| `genuine_100_noteB_daylight` | genuine | ACCEPT | REJECT | 0.0000 | `PERCEPTUAL_NEAR_DUPLICATE_DETECTED` | FAILED |
| `genuine_100_noteB_indoor` | genuine | ACCEPT | REJECT | 0.0000 | `PERCEPTUAL_NEAR_DUPLICATE_DETECTED` | FAILED |
| `genuine_200_noteA_daylight` | genuine | ACCEPT | RESCAN | 0.8068 | `UNCERTAIN_CONFIDENCE_RESCAN_REQUIRED` | FAILED |
| `genuine_200_noteA_indoor` | genuine | ACCEPT | RESCAN | 0.8043 | `UNCERTAIN_CONFIDENCE_RESCAN_REQUIRED` | FAILED |
| `genuine_200_noteB_daylight` | genuine | ACCEPT | RESCAN | 0.8087 | `UNCERTAIN_CONFIDENCE_RESCAN_REQUIRED` | FAILED |
| `genuine_200_noteB_indoor` | genuine | ACCEPT | RESCAN | 0.8040 | `UNCERTAIN_CONFIDENCE_RESCAN_REQUIRED` | FAILED |
| `genuine_500_noteA_daylight` | genuine | ACCEPT | REJECT | 0.0000 | `PERCEPTUAL_NEAR_DUPLICATE_DETECTED` | FAILED |
| `genuine_500_noteA_indoor` | genuine | ACCEPT | REJECT | 0.3000 | `SCREEN_BEZEL_DETECTED` | FAILED |
| `genuine_500_noteB_daylight` | genuine | ACCEPT | REJECT | 0.0000 | `PERCEPTUAL_NEAR_DUPLICATE_DETECTED` | FAILED |
| `genuine_500_noteB_indoor` | genuine | ACCEPT | REJECT | 0.3000 | `SCREEN_BEZEL_DETECTED` | FAILED |
| `screen_negative_10_phone` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_10_monitor` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_20_phone` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_20_monitor` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_50_phone` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_50_monitor` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_100_phone` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_100_monitor` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_200_phone` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_200_monitor` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_500_phone` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `screen_negative_500_monitor` | screen_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_10_color` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_10_photocopy` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_20_color` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_20_photocopy` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_50_color` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_50_photocopy` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_100_color` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_100_photocopy` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_200_color` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_200_photocopy` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_500_color` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `print_negative_500_photocopy` | print_negative | REJECT | REJECT | 0.2500 | `NO_DEVICE_MOTION` | PASSED |
| `duplicate_test_100_rescan` | duplicate | REJECT | REJECT | 0.0000 | `PERCEPTUAL_NEAR_DUPLICATE_DETECTED` | PASSED |
| `duplicate_test_500_rescan` | duplicate | REJECT | REJECT | 0.0000 | `PERCEPTUAL_NEAR_DUPLICATE_DETECTED` | PASSED |
