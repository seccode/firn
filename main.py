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
    for frame in frames:
        print(frame)
    a
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
            f[i][:,:,1]=cv2.add(last,_f[:,:,0])
        else:
            f[i][:,:,1]=_f[:,:,0]
        last=f[i][:,:,1]
    last=None
    for i,_f in enumerate(b):
        if last is not None:
            f[i][:,:,2]=cv2.add(last,_f[:,:,0])
        else:
            f[i][:,:,2]=_f[:,:,0]
        last=f[i][:,:,2]
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
    "-b:v","5M",
    "-preset","slow",
    "-cpu-used","8",
    "-qp","0",
    "out.mp4"
]
subprocess.run(cmd)
#decompress("out.mp4",restored)

