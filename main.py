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

def compress(video_path, output_video):
    """
    Compresses the video by storing the first frame as-is and subsequent frames
    as differences modulo 256 from the previous frame.
    """
    frames = extract_frames(video_path)
    height, width, _ = frames[0].shape
    fps = cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FPS)
    fourcc = 0  # Let OpenCV choose the codec
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # Write the first frame normally
    out.write(frames[0])
    previous_frame = frames[0].astype(np.int16)  # Use int16 to avoid overflow during diff

    # Process subsequent frames
    for frame in tqdm(frames[1:], desc="Processing Frames"):
        # Compute difference and take modulo 256
        diff = frame.astype(np.int16) - previous_frame
        compressed_diff = (diff % 256).astype(np.uint8)  # Wraps around to 0-255
        out.write(compressed_diff)
        # Reconstruct the frame as it will be seen in decompression to keep in sync
        previous_frame = (previous_frame + diff).clip(0, 255).astype(np.int16)

    out.release()
    return len(frames)

def decompress(compressed_video, output_video):
    """
    Decompresses the video by reconstructing frames from differences modulo 256.
    """
    frames = extract_frames(compressed_video)
    previous_frame = frames[0].astype(np.int16)

    # Write the reconstructed frames to an output video
    height, width, _ = frames[0].shape
    fps = cv2.VideoCapture(compressed_video).get(cv2.CAP_PROP_FPS)
    fourcc = 0
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    out.write(frames[0])
    for diff_frame in tqdm(frames[1:], desc="Decompressing Frames"):
        diff = diff_frame.astype(np.int16)  # Treat the stored value as the difference
        # Add the difference and wrap around using modulo 256, then clip to valid range
        current_frame = (previous_frame + diff) % 256
        current_frame = current_frame.astype(np.uint8)  # Ensure uint8 for writing
        previous_frame = current_frame.astype(np.int16)


        out.write(current_frame)
    out.release()

# Paths for input and output videos
video_path = "input.avi"
output_video = "output.avi"
decompressed_video = "decompressed.avi"

# Run the custom compression
num_frames = compress(video_path, output_video)

# Decompress to verify
decompress(output_video, decompressed_video)

# Optional: Apply FFmpeg FFV1 lossless compression
cmd = [
    "ffmpeg", "-i", output_video, "-pix_fmt", "bgr0",
    "-c:v", "ffv1", "-level", "3", "-c:a", "copy", "output_lossless.avi"
]
subprocess.run(cmd)
decompress("output_lossless.avi","restored.avi")
