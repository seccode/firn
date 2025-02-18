import cv2
import numpy as np
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
    fps = cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FPS)
    u=[set(),set(),set()]
    for frame in tqdm(frames, total=len(frames)):
        for i in range(3):
            u[i].update(frame[:,:,i].ravel().tolist())

    sv=[sorted(list(u[i])) for i in range(3)]
    vm=[{val:idx for idx,val in enumerate(sv[i])} for i in range(3)]

    fourcc = cv2.VideoWriter_fourcc(*"AV01")
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    out2 = cv2.VideoWriter("output2.avi", fourcc, fps, (width, height))

    for frame in tqdm(frames, total=len(frames)):
        rf=np.zeros_like(frame)
        for i in range(3):
            rf[:,:,i]=np.vectorize(vm[i].get)(frame[:,:,i])
        out.write(rf)
        out2.write(frame)

    out.release()

# Paths
video_path = "input.mp4"
output_video = "output.avi"

# Run compression
compress(video_path, output_video)
