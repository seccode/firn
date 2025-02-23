import cv2
import numpy as np
import subprocess
from tqdm import tqdm

def extract_frames(video_path):
    """Extracts frames from a video file."""
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

# Algorithm TODO being implemented: track common per channel value changes and replace common changes with lower values
# most common change => 0
# 2nd most common change => 1
def compress(video_path, output_video):
    """
    Compresses the video using a custom differential encoding scheme.

    The first frame is stored normally. For each subsequent frame, the pixel-wise difference
    from the previous frame is computed and mapped as:
      - 0 difference -> 0
      - +1 -> 1
      - -1 -> 2
      - +2 -> 3
      - -2 -> 4
      ... etc.

    Note: This mapping assumes that inter-frame differences remain relatively small.
    """
    frames = extract_frames(video_path)
    height, width, _ = frames[0].shape
    fps = cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FPS)
    fourcc = 0  # Let OpenCV choose the codec
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # Write the first frame normally.
    out.write(frames[0])
    previous_frame = frames[0]

    # Process subsequent frames.
    for frame in tqdm(frames[1:], desc="Processing Frames"):
        # Compute pixel-wise difference (using int16 to accommodate negatives)
        diff = frame.astype(np.int16) - previous_frame.astype(np.int16)

        # Map the differences.
        # For diff == 0, mapped value = 0.
        # For diff > 0, mapped value = 2 * diff - 1.
        # For diff < 0, mapped value = 2 * abs(diff).
        mapped = np.zeros_like(diff, dtype=np.uint8)
        pos_mask = diff > 0
        mapped[pos_mask] = (2 * diff[pos_mask] - 1).clip(0, 255)
        neg_mask = diff < 0
        mapped[neg_mask] = (2 * (-diff[neg_mask])).clip(0, 255)

        out.write(mapped)
        previous_frame = frame

    out.release()
    return len(frames)

def decompress(compressed_video, output_video):
    """
    Decompresses a video compressed with the custom differential encoding scheme.

    The first frame is used directly. For each subsequent frame, the mapped difference is
    reversed:
      - If mapped value is 0 → difference is 0.
      - If the mapped value is odd (1, 3, 5, …) → positive difference = (value + 1) // 2.
      - If the mapped value is even (nonzero) → negative difference = - (value // 2).

    The original frame is reconstructed by adding the difference to the previous frame.
    """
    frames = extract_frames(compressed_video)
    reconstructed_frames = [frames[0]]
    previous_frame = frames[0].astype(np.int16)

    for mapped in tqdm(frames[1:], desc="Decompressing Frames"):
        mapped = mapped.astype(np.int16)
        diff = np.zeros_like(mapped, dtype=np.int16)

        # Odd mapped values indicate a positive difference.
        odd_mask = (mapped % 2 == 1)
        diff[odd_mask] = (mapped[odd_mask] + 1) // 2

        # Even nonzero mapped values indicate a negative difference.
        even_mask = (mapped != 0) & (mapped % 2 == 0)
        diff[even_mask] = - (mapped[even_mask] // 2)

        # Reconstruct the current frame.
        current_frame = previous_frame + diff
        current_frame = np.clip(current_frame, 0, 255).astype(np.uint8)
        reconstructed_frames.append(current_frame)
        previous_frame = current_frame.astype(np.int16)

    # Write the reconstructed frames to an output video.
    height, width, _ = reconstructed_frames[0].shape
    fps = cv2.VideoCapture(compressed_video).get(cv2.CAP_PROP_FPS)
    fourcc = 0
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    for frame in reconstructed_frames:
        out.write(frame)
    out.release()

# Paths for input and output videos.
# Input is an already FFV1 compressed file
video_path = "input.avi"
output_video = "output.avi"

# Run the custom compression.
compress(video_path, output_video)

# Use FFmpeg to apply ffv1 lossless compression.
cmd = [
    "ffmpeg", "-i", output_video, "-pix_fmt", "bgr0",
    "-c:v", "ffv1", "-level", "3", "-c:a", "copy", "output_lossless.avi"
]
subprocess.run(cmd)

