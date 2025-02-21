
import cv2
import numpy as np
from tqdm import tqdm

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
    fps = cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FPS) * 2  # Double FPS

    fourcc = cv2.VideoWriter_fourcc(*"avc1")  # H.264, swap to "FFV1" for lossless
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    out2 = cv2.VideoWriter("output2.mp4", fourcc, fps, (width, height))  # Original reference

    last_remainder = None  # Track previous remainder

    d=[]
    for frame in tqdm(frames, desc="Processing Frames"):
        # Quantize by 2
        frame_q = frame // 2  # Shape: (height, width, 3),
        remainder = frame % 2  # Shape: (height, width, 3),

        # Compute delta based on change from last remainder
        if last_remainder is None:
            delta = remainder  # First frame: delta = remainder (assume last was 0)
        else:
            delta = (remainder!=last_remainder).astype(np.uint8)
        d.append(delta)

        # Second frame: frame_q + delta
        frame_q_with_delta = frame_q + delta

        # Ensure valid range [0, 255]
        frame_q = np.clip(frame_q, 0, 255).astype(np.uint8)
        frame_q_with_delta = np.clip(frame_q_with_delta, 0, 255).astype(np.uint8)

        #Apply this recursively to enhance transformation - might not work with all compressors

        # Write both frames
        out.write(frame_q)

        # Update last remainder
        last_remainder = remainder.copy()

        # Write original for reference
        out2.write(frame)

    for _d in d:
        out.write(_d)
    out.release()
    out2.release()

# Paths
video_path = "input3.mp4"
output_video = "output.mp4"

# Run compression
compress(video_path, output_video)
