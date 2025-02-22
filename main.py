import cv2
import numpy as np
import subprocess
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
    """Compress video by storing per-channel differences in grayscale format"""
    frames = extract_frames(video_path)
    height, width, _ = frames[0].shape
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    # ✅ Use a valid lossless codec for macOS
    fourcc = 0
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height), isColor=False)

    for channel in range(3):  # Process Red, Green, Blue separately
        last = None
        for frame in tqdm(frames, desc=f"Processing Channel {channel}"):
            current_channel = frame[:, :, channel].astype(np.int16)  # Use int16 to handle negatives
            diff_frame = np.zeros((height, width), dtype=np.uint8)

            if last is not None:
                diff = (current_channel - last) % 256  # ✅ Fix wrap-around issue
            else:
                diff = current_channel

            diff_frame[:, :] = diff.astype(np.uint8)
            out.write(diff_frame)
            last = current_channel.copy()  # ✅ Ensure `last` is an independent copy

    out.release()


# Paths
video_path = "input.avi"
output_video = "output.avi"
restored_video = "restored.avi"

# Run compression
compress(video_path, output_video)

cmd = [
    "ffmpeg", "-i", "output.avi",
    "-c:v", "libx265", "-preset", "slow",
    "-x265-params", "lossless=1",
    "-c:a", "copy", "output_lossless.mp4"
]
subprocess.run(cmd)
