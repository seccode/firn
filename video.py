import cv2
import numpy as np

def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()
    return frames

def process_video(video_path, output_video):
    frames = extract_frames(video_path)
    height, width, _ = frames[0].shape

    circle_data = []
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video, fourcc, 30, (width, height))

    for i, frame in enumerate(frames):
        print(f"Processing frame {i+1}/{len(frames)}...")

        blurred_frame=cv2.GaussianBlur(frame,(1,1),0)
        out.write(blurred_frame)
    out.release()
video_path = "input.mov"
output_video = "output.mov"
process_video(video_path, output_video)

