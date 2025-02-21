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
    cap=cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    fourcc=0
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    last_remainder = None  # Track previous remainder
    _frame=np.zeros(frames[0].shape).astype(np.uint8)
    last=None
    for frame in tqdm(frames, desc="Processing Frames"):
        _frame[:,:,0]=frame[:,:,0]
        if last is not None:
            out.write(cv2.subtract(_frame,last))
        else:
            out.write(_frame)
        last=_frame
    _frame=np.zeros(frames[0].shape).astype(np.uint8)
    last=None
    for frame in tqdm(frames, desc="Processing Frames"):
        _frame[:,:,0]=frame[:,:,1]
        if last is not None:
            out.write(cv2.subtract(_frame,last))
        else:
            out.write(_frame)
        last=_frame
    _frame=np.zeros(frames[0].shape).astype(np.uint8)
    last=None
    for frame in tqdm(frames, desc="Processing Frames"):
        _frame[:,:,0]=frame[:,:,2]
        if last is not None:
            out.write(cv2.subtract(_frame,last))
        else:
            out.write(_frame)
        last=_frame
    out.release()

def decompress(compressed_video, output_video):
    frames = extract_frames(compressed_video)
    total_frames = len(frames)
    s=int(total_frames/3)
    r=frames[:s]
    g=frames[s:-s]
    b=frames[-s:]
    height, width, _ = frames[0].shape
    fps = cv2.VideoCapture(compressed_video).get(cv2.CAP_PROP_FPS)  # Undo the FPS doubling
    fourcc = 0
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    f=[np.zeros(frames[0].shape).astype(np.uint8) for _ in range(total_frames)]
    last=None
    for i,_f in enumerate(r):
        if last is not None:
            f[i][:,:,0]=cv2.add(last,_f[:,:,0])
        else:
            f[i][:,:,0]=_f[:,:,0]
        last=f[i][:,:,0]
    last=None
    for i,_f in enumerate(g):
        if last is not None:
            f[i][:,:,0]=cv2.add(last,_f[:,:,0])
        else:
            f[i][:,:,0]=_f[:,:,0]
        last=f[i][:,:,0]
    last=None
    for i,_f in enumerate(b):
        if last is not None:
            f[i][:,:,0]=cv2.add(last,_f[:,:,0])
        else:
            f[i][:,:,0]=_f[:,:,0]
        last=f[i][:,:,0]
    for _f in f:
        out.write(_f)
    out.release()

video_path = "input4.mp4"
output_video = "output.avi"
restored="restored.avi"


# Run compression
compress(video_path, output_video)
cmd=[
    "ffmpeg",
    "-i", output_video,
    "-c:v", "libaom-av1",
    "-crf", "18",
    "-b:v","5M",
    "-preset","ultrafast",
    "-cpu-used","4",
    "-g","240",
    "-keyint_min","240",
    "-tile-columns","2",
    "-tile-rows","2",
    "-row-mt","1",
    "out.mp4"
]
subprocess.run(cmd)
cmd=[
    "ffmpeg",
    "-i", video_path,
    "-c:v", "libaom-av1",
    "-crf", "18",
    "-b:v","5M",
    "-preset","ultrafast",
    "-cpu-used","4",
    "-g","240",
    "-keyint_min","240",
    "-tile-columns","2",
    "-tile-rows","2",
    "-row-mt","1",
    "output2.mp4"
]
subprocess.run(cmd)
decompress("out.mp4",restored)

