import cv2
import numpy as np
from tqdm import tqdm

# Original lookup table for remainder-based compensation
COMPENSATION_TABLE = np.array([
    (0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
    (1, 1, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1),
    (0, 2, 0), (0, 0, 2), (2, 0, 0), (0, 1, 2),
    (2, 1, 0), (2, 0, 1), (1, 0, 2), (1, 2, 0)
], dtype=np.uint8)

# **Precompute rearranged lookup tables for each possible remainder value**
REARRANGED_TABLES = np.array([np.roll(COMPENSATION_TABLE, shift=-i, axis=0) for i in range(16)], dtype=np.uint8)

def extract_frames(video_path):
    """Extracts frames from a video file"""
    cap = cv2.VideoCapture(video_path)
    frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()
    return frames

def compress(video_path, output_video):
    frames = extract_frames(video_path)
    height, width, _ = frames[0].shape
    fps = cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FPS) * 2  # Double FPS since we add frames

    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    out2 = cv2.VideoWriter("output2.mp4", fourcc, fps, (width, height))

    last_remainder = None  # Stores the previous remainder data for each pixel

    for frame_index, frame in tqdm(enumerate(frames), total=len(frames), desc="Processing Frames"):
        # Compute quantized frame
        frame_q = frame // 16

        # Compute remainder
        remainder = frame % 16  # Shape: (height, width, 3)

        # Create compensation frame
        compensation_frame = frame_q.copy()

        if last_remainder is not None:
            # Select rearranged table for each pixel using its last remainder
            rearranged_compensation = np.zeros_like(compensation_frame)

            for i in range(3):  # R, G, B channels
                # Corrected indexing: Get compensation value for each pixel
                pixel_indices = last_remainder[:, :, i]  # Get last remainders
                rearranged_compensation[:, :, i] = REARRANGED_TABLES[pixel_indices, pixel_indices, i]

            # Apply compensation
            compensation_frame += rearranged_compensation
        else:
            # First compensation frame uses the normal COMPENSATION_TABLE
            for i in range(3):  # R, G, B channels
                compensation_frame[:, :, i] += COMPENSATION_TABLE[remainder[:, :, i], i]

        # Store current remainder for the next frame
        last_remainder = remainder.copy()

        # Ensure values remain in valid range [0, 255]
        compensation_frame = np.clip(compensation_frame, 0, 255).astype(np.uint8)

        # Write both frames: quantized and compensation frame
        out.write(frame_q)
        out.write(compensation_frame)

        out2.write(frame)  # Original frame output for reference

    out.release()
    out2.release()

# Paths
video_path = "input3.mp4"
output_video = "output.mp4"

# Run compression
compress(video_path, output_video)

