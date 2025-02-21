import cv2
import numpy as np
from tqdm import tqdm

def extract_frames(video_path):
    """Extracts frames from a video file with no color conversion"""
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        raise ValueError(f"No frames extracted from {video_path}")
    return frames

def compress(video_path, output_bin):
    """Stores raw frame differences in a binary file"""
    frames = extract_frames(video_path)
    if not frames:
        raise ValueError("No frames extracted from video")

    height, width, _ = frames[0].shape
    num_frames = len(frames)

    with open(output_bin, "wb") as f:
        # Store width, height, and frame count
        f.write(np.array([width, height, num_frames], dtype=np.int32).tobytes())

        for channel in range(3):
            last = None
            for i, frame in enumerate(tqdm(frames, desc=f"Compressing Channel {channel}")):
                current_channel = frame[:, :, channel].astype(np.uint8)

                if last is None:
                    f.write(current_channel.tobytes())
                else:
                    diff_channel = ((current_channel.astype(np.int16) - last.astype(np.int16)) % 256).astype(np.uint8)
                    f.write(diff_channel.tobytes())

                last = current_channel.copy()

def decompress(compressed_bin, output_video, fps=30):
    """Reconstructs video from binary frame differences"""
    with open(compressed_bin, "rb") as f:
        # Read metadata
        width, height, num_frames = np.frombuffer(f.read(12), dtype=np.int32)

        reconstructed_frames = [np.zeros((height, width, 3), dtype=np.uint8) for _ in range(num_frames)]

        for channel in range(3):
            last = None
            for i in range(num_frames):
                raw_bytes = f.read(height * width)
                if len(raw_bytes) != height * width:
                    raise ValueError(f"Error: Unexpected data size for frame {i} (Channel {channel})")

                diff_channel = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((height, width))

                if last is None:
                    reconstructed_frames[i][:, :, channel] = diff_channel
                else:
                    recon_channel = ((last.astype(np.int16) + diff_channel.astype(np.int16)) % 256).astype(np.uint8)
                    reconstructed_frames[i][:, :, channel] = recon_channel

                last = reconstructed_frames[i][:, :, channel].copy()

    # Save reconstructed frames to video using FFmpeg
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    for frame in reconstructed_frames:
        out.write(frame)
    out.release()

# Run compression and decompression
video_path = "input4.mp4"
compressed_bin = "compressed.bin"
output_video = "restored.avi"

compress(video_path, compressed_bin)
decompress(compressed_bin, output_video)

