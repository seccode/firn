import cv2
import numpy as np
import subprocess
from tqdm import tqdm
from collections import Counter

def extract_frames(video_path, as_grayscale=False):
    """Extracts frames from a video file, optionally as grayscale"""
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if as_grayscale and frame.ndim == 3:  # If frame is RGB, convert to grayscale
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frames.append(frame)
    cap.release()
    return frames

def compress(video_path, output_video):
    frames = extract_frames(video_path)  # Read as RGB
    height, width, _ = frames[0].shape
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    fourcc = 0

    # First pass: Compute differences and build frequency counter
    temp_video = "output.avi"
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height), isColor=False)  # Grayscale output
    value_counts = Counter()

    # Red channel differences
    _frame = np.zeros((height, width), dtype=np.uint8)
    last = None
    for frame in tqdm(frames, desc="Pass 1: Red Frames"):
        _frame[:] = frame[:,:,0]
        if last is not None:
            diff = cv2.subtract(_frame, last) % 255
        else:
            diff = _frame.copy()
        value_counts.update(diff.ravel())
        out.write(diff)
        last = _frame.copy()

    # Green channel differences
    _frame = np.zeros((height, width), dtype=np.uint8)
    last = None
    for frame in tqdm(frames, desc="Pass 1: Green Frames"):
        _frame[:] = frame[:,:,1]
        if last is not None:
            diff = cv2.subtract(_frame, last) % 255
        else:
            diff = _frame.copy()
        value_counts.update(diff.ravel())
        out.write(diff)
        last = _frame.copy()

    # Blue channel differences
    _frame = np.zeros((height, width), dtype=np.uint8)
    last = None
    for frame in tqdm(frames, desc="Pass 1: Blue Frames"):
        _frame[:] = frame[:,:,2]
        if last is not None:
            diff = cv2.subtract(_frame, last) % 255
        else:
            diff = _frame.copy()
        value_counts.update(diff.ravel())
        out.write(diff)
        last = _frame.copy()

    out.release()

def decompress(compressed_video, output_video, substitution_map):
    frames = extract_frames(compressed_video, as_grayscale=True)  # Read as grayscale
    total_frames = len(frames)
    s = int(total_frames / 3)
    r = frames[:s]  # Red differences
    g = frames[s:2*s]  # Green differences
    b = frames[2*s:]  # Blue differences
    height, width = frames[0].shape  # Grayscale frames are 2D
    fps = cv2.VideoCapture(compressed_video).get(cv2.CAP_PROP_FPS)
    fourcc = 0
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))  # RGB output

    # Reverse substitution map
    reverse_map = {idx: val for val, idx in substitution_map.items()}

    # Reconstruct frames
    f = [np.zeros((height, width, 3), dtype=np.uint8) for _ in range(s)]

    # Red channel
    last = None
    for i, _f in enumerate(r):
        unsubstituted = np.array([reverse_map[val] for val in _f.ravel()], dtype=np.uint8).reshape(height, width)
        if last is not None:
            f[i][:,:,0] = cv2.add(last, unsubstituted) % 255
        else:
            f[i][:,:,0] = unsubstituted
        last = f[i][:,:,0].copy()

    # Green channel
    last = None
    for i, _f in enumerate(g):
        unsubstituted = np.array([reverse_map[val] for val in _f.ravel()], dtype=np.uint8).reshape(height, width)
        if last is not None:
            f[i][:,:,1] = cv2.add(last, unsubstituted) % 255
        else:
            f[i][:,:,1] = unsubstituted
        last = f[i][:,:,1].copy()

    # Blue channel
    last = None
    for i, _f in enumerate(b):
        unsubstituted = np.array([reverse_map[val] for val in _f.ravel()], dtype=np.uint8).reshape(height, width)
        if last is not None:
            f[i][:,:,2] = cv2.add(last, unsubstituted) % 255
        else:
            f[i][:,:,2] = unsubstituted
        last = f[i][:,:,2].copy()

    # Write reconstructed RGB frames
    for _f in f:
        out.write(_f)
    out.release()

# Paths
video_path = "input.avi"
output_video = "output.avi"
restored_video = "restored.avi"

# Run compression
substitution_map = compress(video_path, output_video)
cmd = [
    "ffmpeg", "-i", "output.avi",
    "-c:v", "libx265", "-preset", "slow",
    "-x265-params", "lossless=1",
    "-c:a", "copy", "output_lossless.mp4"
]
subprocess.run(cmd)

# Run decompression
#decompress("output_lossless.mp4", restored_video, substitution_map)
