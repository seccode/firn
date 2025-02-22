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
                diff = ((current_channel - last) + 256) % 256  # ✅ Fix wrap-around issue
            else:
                diff = current_channel

            diff_frame[:, :] = diff.astype(np.uint8)
            out.write(diff_frame)
            last = current_channel.copy()  # ✅ Ensure `last` is an independent copy

    out.release()

def decompress(compressed_video, output_video):
    """Decompress video by reconstructing original frames"""
    frames = extract_frames(compressed_video)
    total_frames = len(frames)
    s = total_frames // 3  # Number of original frames

    r_frames = frames[:s]      # Red channel frames
    g_frames = frames[s:2*s]   # Green channel frames
    b_frames = frames[2*s:]    # Blue channel frames

    height, width = r_frames[0].shape
    fps = cv2.VideoCapture(compressed_video).get(cv2.CAP_PROP_FPS)

    # ✅ Use a valid lossless codec
    fourcc = 0
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # Initialize reconstructed frames
    f = [np.zeros((height, width, 3), dtype=np.uint8) for _ in range(s)]

    last_r = last_g = last_b = None

    for i, (r, g, b) in enumerate(zip(r_frames, g_frames, b_frames)):
        # ✅ Properly decode difference values
        r_decoded = ((r.astype(np.int16) + (last_r if last_r is not None else 0)) % 256).astype(np.uint8)
        g_decoded = ((g.astype(np.int16) + (last_g if last_g is not None else 0)) % 256).astype(np.uint8)
        b_decoded = ((b.astype(np.int16) + (last_b if last_b is not None else 0)) % 256).astype(np.uint8)

        f[i][:, :, 0] = r_decoded
        f[i][:, :, 1] = g_decoded
        f[i][:, :, 2] = b_decoded

        last_r, last_g, last_b = r_decoded.copy(), g_decoded.copy(), b_decoded.copy()

    for frame in f:
        out.write(frame)

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

# Run decompression
decompress(output_video, restored_video)

