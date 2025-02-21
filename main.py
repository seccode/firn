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
    frames = extract_frames(video_path)
    height, width, _ = frames[0].shape
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    fourcc = cv2.VideoWriter_fourcc(*"FFV1")  # Ensure lossless codec
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    last = None
    for channel in range(3):  # Process R, G, B separately
        _frame = np.zeros(frames[0].shape, dtype=np.uint8)
        for frame in tqdm(frames, desc=f"Processing Channel {channel}"):
            _frame[:, :, 0] = frame[:, :, channel]
            if last is not None:
                diff = cv2.subtract(_frame.astype(np.int16), last.astype(np.int16)).clip(0, 255).astype(np.uint8)
                out.write(diff)
            else:
                out.write(_frame)
            last = _frame.copy()
    out.release()


def decompress(compressed_video, output_video):
    frames = extract_frames(compressed_video)
    total_frames = len(frames)
    s = total_frames // 3  # Ensure exact division

    r = frames[:s]
    g = frames[s:2*s]
    b = frames[2*s:]

    height, width, _ = frames[0].shape
    fps = cv2.VideoCapture(compressed_video).get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*"FFV1")  # Ensure same codec as compression
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    f = [np.zeros(frames[0].shape, dtype=np.uint8) for _ in range(s)]

    last = None
    for i, _f in enumerate(r):
        if last is not None:
            f[i][:,:,0] = cv2.add(last.astype(np.int16), _f[:,:,0].astype(np.int16)).clip(0, 255).astype(np.uint8)
        else:
            f[i][:,:,0] = _f[:,:,0]
        last = f[i][:,:,0]

    last = None
    for i, _f in enumerate(g):
        if last is not None:
            f[i][:,:,1] = cv2.add(last.astype(np.int16), _f[:,:,0].astype(np.int16)).clip(0, 255).astype(np.uint8)
        else:
            f[i][:,:,1] = _f[:,:,0]
        last = f[i][:,:,1]

    last = None
    for i, _f in enumerate(b):
        if last is not None:
            f[i][:,:,2] = cv2.add(last.astype(np.int16), _f[:,:,0].astype(np.int16)).clip(0, 255).astype(np.uint8)
        else:
            f[i][:,:,2] = _f[:,:,0]
        last = f[i][:,:,2]

    for _f in f:
        out.write(_f)
    out.release()


video_path = "input4.mp4"
output_video = "output.avi"
restored = "restored.avi"
compress(video_path, output_video)
decompress(output_video,restored)

