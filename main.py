import cv2
import numpy as np
import subprocess
from tqdm import tqdm
import zstandard as zstd

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

# Can be recursively applied to quantized frames for greater effect
def compress(video_path, output_video):
    frames = extract_frames(video_path)
    height, width, _ = frames[0].shape
    fps = cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FPS)

    fourcc = 0
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    last_remainder = None  # Track previous remainder

    d=[]
    x=[]
    i=0
    j=0
    for frame in tqdm(frames, desc="Processing Frames"):
        # Quantize by 2
        frame_q = frame // 2  # Shape: (height, width, 3),
        remainder = frame % 2  # Shape: (height, width, 3),

        # Compute delta based on change from last remainder
        if last_remainder is None:
            delta = remainder  # First frame: delta = remainder (assume last was 0)
        else:
            delta = (remainder!=last_remainder).astype(np.uint8)
        if np.array_equal(remainder, last_remainder):
            i+=1
        else:
            x.append(chr(i))
            i=0
            d.append(delta)

        # Second frame: frame_q + delta
        frame_q_with_delta = frame_q + delta

        # Ensure valid range [0, 255]
        frame_q = np.clip(frame_q, 0, 255).astype(np.uint8)
        frame_q_with_delta = np.clip(frame_q_with_delta, 0, 255).astype(np.uint8)

        # Write both frames
        out.write(frame_q)

        # Update last remainder
        last_remainder = remainder.copy()

        # Write original for reference

        j+=1
    for _d in d:
        out.write(_d)
    out.release()
    f=open("x","wb")
    f.write(zstd.compress("".join(x).encode(),level=22))
    f.close()
    return j

def decompress(compressed_video, output_video):
    """Decompresses the video compressed with the custom algorithm"""
    # Extract all frames from compressed video
    frames = extract_frames(compressed_video)
    total_frames = len(frames)

    # Calculate split point (original frames followed by delta frames)
    original_frame_count = total_frames // 2
    quantized_frames = frames[:original_frame_count]
    delta_frames = frames[original_frame_count:]

    # Get video properties
    height, width, _ = quantized_frames[0].shape
    fps = cv2.VideoCapture(compressed_video).get(cv2.CAP_PROP_FPS) / 2  # Undo the FPS doubling

    # Setup output video writer
    fourcc = 0
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # Process frames
    last_remainder = None

    for i in tqdm(range(len(quantized_frames)), desc="Decompressing Frames"):
        # Get current quantized frame and corresponding delta
        frame_q = quantized_frames[i]
        delta = delta_frames[i]

        # Handle edge cases from lossy compression
        # Quantized frames should be in range [0, 127]
        frame_q = np.clip(frame_q, 0, 127).astype(np.uint8)

        # Delta frames should be binary (0 or 1)
        delta = np.where(delta > 0, 1, 0).astype(np.uint8)

        # Reconstruct remainder
        if last_remainder is None:
            remainder = delta  # First frame uses delta directly
        else:
            # Update remainder based on delta (change indicator)
            remainder = np.where(delta == 1,
                               1 - last_remainder,  # Flip the bit if delta = 1
                               last_remainder).astype(np.uint8)

        # Reconstruct original frame
        # Multiply quantized value by 2 and add remainder
        reconstructed_frame = (frame_q * 2 + remainder)

        # Ensure output is in valid range [0, 255]
        reconstructed_frame = np.clip(reconstructed_frame, 0, 255).astype(np.uint8)

        # Write reconstructed frame
        out.write(reconstructed_frame)

        # Update last_remainder for next iteration
        last_remainder = remainder.copy()

    out.release()

# Paths
video_path = "input.avi"
output_video = "output.avi"

# Run compression
compress(video_path, output_video)

cmd = [
    "ffmpeg","-i",output_video,"-pix_fmt","bgr0","-c:v","ffv1","-level","3","-c:a","copy","output_lossless.avi"
]

# Run FFmpeg command
subprocess.run(cmd)

