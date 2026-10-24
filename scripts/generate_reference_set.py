import os
import json
import time
import numpy as np
import cv2

REFERENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reference")
PROFILES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "profiles", "inr.json")

DENOM_COLORS = {
    10: (35, 65, 115),     # Chocolate Brown (BGR)
    20: (40, 160, 190),    # Greenish Yellow
    50: (190, 140, 40),    # Fluorescent Blue
    100: (170, 110, 140),  # Lavender
    200: (30, 185, 240),   # Bright Yellow
    500: (120, 125, 115)   # Stone Grey
}

ASPECT_RATIOS = {
    10: 1.952,
    20: 2.048,
    50: 2.045,
    100: 2.152,
    200: 2.212,
    500: 2.273
}

def create_base_note(denom: int, serial: str, side: str = "front", tilt_angle: float = 0.0) -> np.ndarray:
    ar = ASPECT_RATIOS.get(denom, 2.1)
    height = 500
    width = int(height * ar)
    base_color = DENOM_COLORS.get(denom, (120, 120, 120))

    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = base_color

    # Add realistic paper substrate fibre texture (cotton rag micro-variance)
    noise = np.random.normal(0, 12, (height, width, 3)).astype(np.int16)
    img_noisy = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = img_noisy

    # White watermark window (left side)
    wm_x1 = int(width * 0.06)
    wm_x2 = int(width * 0.28)
    wm_y1 = int(height * 0.15)
    wm_y2 = int(height * 0.85)
    
    cv2.rectangle(img, (wm_x1, wm_y1), (wm_x2, wm_y2), (235, 235, 230), -1)
    # Subtle watermark portrait shading
    cv2.circle(img, (int((wm_x1+wm_x2)/2), int((wm_y1+wm_y2)/2)), 60, (215, 215, 210), -1)
    cv2.putText(img, str(denom), (wm_x1 + 40, wm_y2 - 30), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (200, 200, 195), 2)

    # Security thread (vertical band around x = 0.44)
    thread_x = int(width * 0.44)
    thread_w = int(width * 0.018)
    
    # Thread color shift across tilt angle for 100, 200, 500
    if denom in [100, 200, 500]:
        # Green to blue shift
        hue_shift = int(35 + tilt_angle * 40)
        thread_color = (hue_shift, 140, 40)
    else:
        thread_color = (60, 60, 60)

    # Windowed segments
    for y_seg in range(20, height - 20, 45):
        cv2.rectangle(img, (thread_x, y_seg), (thread_x + thread_w, y_seg + 25), thread_color, -1)
        cv2.putText(img, "RBI", (thread_x - 5, y_seg + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (240, 240, 240), 1)

    # Mahatma Gandhi Portrait (right-center area)
    p_x1 = int(width * 0.50)
    p_x2 = int(width * 0.76)
    p_y1 = int(height * 0.18)
    p_y2 = int(height * 0.82)

    # Intaglio portrait shading
    cv2.ellipse(img, (int((p_x1+p_x2)/2), int((p_y1+p_y2)/2)), (80, 120), 0, 0, 360, (50, 40, 30), 2)
    cv2.circle(img, (int((p_x1+p_x2)/2), int((p_y1+p_y2)/2) - 20), 45, (60, 50, 40), -1)
    cv2.putText(img, "MAHATMA GANDHI", (p_x1 + 10, p_y2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 30, 20), 1)

    # Large Denomination Numerals
    cv2.putText(img, str(denom), (int(width * 0.78), int(height * 0.88)), cv2.FONT_HERSHEY_DUPLEX, 1.8, (25, 25, 20), 3)
    cv2.putText(img, str(denom), (int(width * 0.04), int(height * 0.28)), cv2.FONT_HERSHEY_DUPLEX, 1.4, (25, 25, 20), 2)

    # Dual Serial Panels
    # Top-Left serial panel
    cv2.putText(img, serial, (int(width * 0.08), int(height * 0.16)), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
    # Bottom-Right serial panel
    cv2.putText(img, serial, (int(width * 0.68), int(height * 0.90)), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (20, 20, 20), 2)

    # RBI Header text and microtext lines
    cv2.putText(img, "RESERVE BANK OF INDIA", (int(width * 0.30), int(height * 0.12)), cv2.FONT_HERSHEY_TRIPLEX, 0.85, (30, 25, 20), 2)
    cv2.putText(img, "GUARANTEED BY THE CENTRAL GOVERNMENT", (int(width * 0.32), int(height * 0.18)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (50, 40, 30), 1)

    # See-through register
    cv2.rectangle(img, (15, int(height * 0.45)), (40, int(height * 0.55)), (100, 90, 80), 2)
    cv2.putText(img, str(denom)[0], (20, int(height * 0.52)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 30, 20), 2)

    # Border frame
    cv2.rectangle(img, (4, 4), (width - 4, height - 4), (40, 35, 30), 2)

    return img

def embed_in_scene(
    note_img: np.ndarray,
    tilt_step: int,
    medium_type: str = "genuine",
    lighting: str = "daylight"
) -> np.ndarray:
    scene_h, scene_w = 720, 1280
    scene = np.full((scene_h, scene_w, 3), 50, dtype=np.uint8)

    # Lighting background
    if lighting == "indoor":
        scene[:, :] = (45, 55, 65)  # Warmer indoor tint
    else:
        scene[:, :] = (65, 65, 60)  # Cooler daylight

    nh, nw, _ = note_img.shape
    scale = 0.82
    scaled_w = int(nw * scale)
    scaled_h = int(nh * scale)
    scaled_note = cv2.resize(note_img, (scaled_w, scaled_h))

    # Calculate tilt warp
    angle_deg = (tilt_step - 2.5) * 4.0
    rad = np.radians(angle_deg)
    
    # 4 points for perspective warp
    offset_y = int(np.sin(rad) * 40)
    src_pts = np.float32([[0, 0], [scaled_w, 0], [scaled_w, scaled_h], [0, scaled_h]])
    dst_pts = np.float32([
        [0, max(0, offset_y)],
        [scaled_w, max(0, -offset_y)],
        [scaled_w - 10, scaled_h + min(0, -offset_y)],
        [10, scaled_h + min(0, offset_y)]
    ])

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_note = cv2.warpPerspective(scaled_note, M, (scaled_w, scaled_h + abs(offset_y) * 2))

    wn_h, wn_w, _ = warped_note.shape
    start_x = (scene_w - wn_w) // 2
    start_y = (scene_h - wn_h) // 2

    # Medium specific artifacts
    if medium_type == "screen":
        # 1. Phone / Monitor Bezel around note
        bezel_pad = 28
        cv2.rectangle(
            scene,
            (start_x - bezel_pad, start_y - bezel_pad),
            (start_x + wn_w + bezel_pad, start_y + wn_h + bezel_pad),
            (15, 15, 15),
            -1
        )
        cv2.rectangle(
            scene,
            (start_x - bezel_pad, start_y - bezel_pad),
            (start_x + wn_w + bezel_pad, start_y + wn_h + bezel_pad),
            (80, 80, 80),
            2
        )

        # 2. Add Moire / Pixel Grid to note
        grid = np.zeros_like(warped_note)
        grid[::3, :, :] = 50   # Horizontal scanlines
        grid[:, ::3, :] += 50  # Vertical subpixel columns
        moire_fringe = (25 * np.sin(np.linspace(0, 30 * np.pi, wn_w))).astype(np.int16)
        warped_note = np.clip(warped_note.astype(np.int16) + grid + moire_fringe[:, None], 0, 255).astype(np.uint8)

    elif medium_type == "print":
        # 1. Flat paper with Halftone Rosette screening
        y_coords, x_coords = np.ogrid[:wn_h, :wn_w]
        halftone = (35 * (np.sin(x_coords * 0.8) * np.cos(y_coords * 0.8))).astype(np.int16)
        # Reduced contrast and dynamic range typical of toner/inkjet
        washed_out = cv2.convertScaleAbs(warped_note, alpha=0.88, beta=25)
        warped_note = np.clip(washed_out.astype(np.int16) + halftone[:, :, None], 0, 255).astype(np.uint8)

    # Place note into scene
    mask = (warped_note > 10).any(axis=2)
    roi = scene[start_y:start_y + wn_h, start_x:start_x + wn_w]
    roi[mask] = warped_note[mask]

    # Specular ambient highlight across tilt
    if medium_type == "genuine":
        glare_layer = np.zeros_like(scene, dtype=np.float32)
        glare_x = int(start_x + (tilt_step / 5.0) * wn_w)
        cv2.line(glare_layer, (glare_x, start_y), (glare_x + 40, start_y + wn_h), (70, 70, 60), 32)
        glare_blurred = cv2.GaussianBlur(glare_layer, (25, 25), 0)
        note_mask = np.zeros((scene_h, scene_w), dtype=bool)
        note_mask[start_y:start_y + wn_h, start_x:start_x + wn_w] = mask
        scene[note_mask] = np.clip(scene[note_mask].astype(np.float32) + glare_blurred[note_mask], 0, 255).astype(np.uint8)

    return scene

def generate_sample_set(
    sample_id: str,
    denom: int,
    serial: str,
    medium_type: str,
    lighting: str,
    is_duplicate: bool = False
) -> dict:
    sample_dir = os.path.join(REFERENCE_DIR, sample_id)
    os.makedirs(sample_dir, exist_ok=True)

    base_note = create_base_note(denom, serial)
    timestamps = []
    gyro_samples = []
    accel_samples = []

    start_ms = int(time.time() * 1000)

    for i in range(6):
        tilt_val = (i - 2.5) / 2.5  # -1.0 to +1.0
        frame = embed_in_scene(base_note, i, medium_type, lighting)
        frame_path = os.path.join(sample_dir, f"frame_{i}.png")
        cv2.imwrite(frame_path, frame)

        t_ms = start_ms + i * 420  # ~2.1 seconds total
        timestamps.append(t_ms)

        if medium_type == "genuine":
            # Realistic device tilt gyro & accel (natural hand movement ~0.15-0.35 rad/s)
            gyro_samples.append({
                "timestamp_ms": t_ms,
                "x": float(0.25 * np.sin(i * 1.1)),
                "y": float(0.38 * np.cos(i * 1.1)),
                "z": float(0.15 * np.sin(i * 0.7))
            })
            accel_samples.append({
                "timestamp_ms": t_ms,
                "x": float(0.85 * np.sin(i * 0.9)),
                "y": float(9.65 + 0.45 * np.cos(i * 0.8)),
                "z": float(1.20 + 0.40 * i)
            })
        else:
            # Low/static motion on screens / prints / photocopies
            gyro_samples.append({"timestamp_ms": t_ms, "x": 0.005, "y": 0.005, "z": 0.005})
            accel_samples.append({"timestamp_ms": t_ms, "x": 0.01, "y": 9.81, "z": 0.01})

    metadata = {
        "sample_id": sample_id,
        "denomination": denom,
        "serial": serial,
        "medium_type": medium_type,
        "lighting": lighting,
        "frame_count": 6,
        "duration_ms": timestamps[-1] - timestamps[0],
        "frame_timestamps_ms": timestamps,
        "gyroscope_samples": gyro_samples,
        "accelerometer_samples": accel_samples
    }

    with open(os.path.join(sample_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {
        "path": f"reference/{sample_id}",
        "label": "duplicate" if is_duplicate else ("genuine" if medium_type == "genuine" else f"{medium_type}_negative"),
        "denomination": denom,
        "serial": serial,
        "conditions": f"{medium_type}, {lighting}, tilt",
        "expected_decision": "REJECT" if (medium_type != "genuine" or is_duplicate) else "ACCEPT"
    }

def main():
    os.makedirs(REFERENCE_DIR, exist_ok=True)
    manifest = []

    denominations = [10, 20, 50, 100, 200, 500]

    # 1. Genuine Notes (2 or more different notes per denomination, daylight & indoor)
    for denom in denominations:
        for idx, (letter, serial_num) in enumerate([("A", "102938"), ("B", "584920")]):
            serial = f"{denom//10:02d}{letter} {serial_num}"
            # Daylight
            s_day = generate_sample_set(
                sample_id=f"genuine_{denom}_note{letter}_daylight",
                denom=denom,
                serial=serial,
                medium_type="genuine",
                lighting="daylight"
            )
            manifest.append(s_day)

            # Indoor
            s_in = generate_sample_set(
                sample_id=f"genuine_{denom}_note{letter}_indoor",
                denom=denom,
                serial=serial,
                medium_type="genuine",
                lighting="indoor"
            )
            manifest.append(s_in)

    # 2. Screen Negatives (10 or more: each denom on phone and monitor)
    for denom in denominations:
        s_phone = generate_sample_set(
            sample_id=f"screen_negative_{denom}_phone",
            denom=denom,
            serial=f"{denom//10:02d}S 888123",
            medium_type="screen",
            lighting="indoor"
        )
        manifest.append(s_phone)

        s_mon = generate_sample_set(
            sample_id=f"screen_negative_{denom}_monitor",
            denom=denom,
            serial=f"{denom//10:02d}M 999456",
            medium_type="screen",
            lighting="daylight"
        )
        manifest.append(s_mon)

    # 3. Print Negatives (10 or more: colour prints and photocopies)
    for denom in denominations:
        s_print = generate_sample_set(
            sample_id=f"print_negative_{denom}_color",
            denom=denom,
            serial=f"{denom//10:02d}P 777321",
            medium_type="print",
            lighting="daylight"
        )
        manifest.append(s_print)

        s_copy = generate_sample_set(
            sample_id=f"print_negative_{denom}_photocopy",
            denom=denom,
            serial=f"{denom//10:02d}C 666789",
            medium_type="print",
            lighting="indoor"
        )
        manifest.append(s_copy)

    # 4. Duplicate Scans (re-scanning the same note twice)
    dup1 = generate_sample_set(
        sample_id="duplicate_test_100_rescan",
        denom=100,
        serial="10A 102938",  # matches genuine_100_noteA_daylight
        medium_type="genuine",
        lighting="daylight",
        is_duplicate=True
    )
    manifest.append(dup1)

    dup2 = generate_sample_set(
        sample_id="duplicate_test_500_rescan",
        denom=500,
        serial="50A 102938",  # matches genuine_500_noteA_daylight
        medium_type="genuine",
        lighting="indoor",
        is_duplicate=True
    )
    manifest.append(dup2)

    manifest_file = os.path.join(REFERENCE_DIR, "manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(manifest)} reference sample sets and wrote manifest to {manifest_file}")

if __name__ == "__main__":
    main()
