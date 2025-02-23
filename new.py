import cv2
import numpy as np

def compress_adjacent(input_path, output_path):
    """
    Compress video by comparing adjacent pixels:
    - If left pixel equals right pixel, set right to 0
    - Processes each color channel separately
    Produces same number of frames as input
    """

    # Open input video to get properties
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open input video: {input_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if total_frames <= 0:
        raise ValueError("Could not determine number of frames (or zero frames).")

    # Prepare output writer
    fourcc = cv2.VideoWriter_fourcc(*"FFV1")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        raise IOError(f"Cannot open output video for writing: {output_path}")

    print(f"[compress_adjacent] Processing {total_frames} frames.")

    # Process video
    cap = cv2.VideoCapture(input_path)
    frame_count = 0

    while True:
        print(frame_count)
        ret, frame = cap.read()
        if not ret:
            break

        # Create output frame
        compressed_frame = np.copy(frame)

        # Process each color channel (BGR order in OpenCV)
        for channel in range(3):
            # Get current channel
            channel_data = compressed_frame[..., channel]

            # Compare adjacent pixels horizontally
            for y in range(height):
                for x in range(1, width):
                    left_pixel = channel_data[y, x-1]
                    right_pixel = channel_data[y, x]

                    # If left equals right, set right to 0
                    if left_pixel == right_pixel:
                        channel_data[y, x] = 0

        out.write(compressed_frame)
        frame_count += 1

    cap.release()
    out.release()
    print(f"[compress_adjacent] Processed {frame_count} frames.")

def decompress_adjacent(compressed_path, output_path):
    """
    Decompress video by restoring adjacent pixel values:
    - If right pixel is 0 and left is not 0, set right to left value
    - Processes each color channel separately
    """
    cap = cv2.VideoCapture(compressed_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open compressed video: {compressed_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    print(f"[decompress_adjacent] Processing {total_frames} frames.")

    # Prepare output writer
    fourcc = cv2.VideoWriter_fourcc(*"FFV1")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        raise IOError(f"Cannot open output video for writing: {output_path}")

    # Process video
    cap = cv2.VideoCapture(compressed_path)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Create output frame
        decompressed_frame = np.copy(frame)

        # Process each color channel
        for channel in range(3):
            channel_data = decompressed_frame[..., channel]

            # Restore values horizontally
            for y in range(height):
                for x in range(1, width):
                    left_pixel = channel_data[y, x-1]
                    right_pixel = channel_data[y, x]

                    # If right is 0 and left is not 0, copy left to right
                    if right_pixel == 0 and left_pixel != 0:
                        channel_data[y, x] = left_pixel

        out.write(decompressed_frame)
        frame_count += 1

    cap.release()
    out.release()
    print(f"[decompress_adjacent] Restored {frame_count} frames.")

def main():
    input_video = "input.mp4"
    compressed_video = "compressed.avi"
    decompressed_video = "restored.avi"

    # Compress using adjacent pixel comparison
    compress_adjacent(input_video, compressed_video)

    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", compressed_video,
        "-c:v", "libaom-av1",
        "-crf", "27",
        "-b:v", "0",
        "-cpu-used", "8",
        "out2.mp4"
    ])


    decompress_adjacent(compressed_video, decompressed_video)

if __name__ == "__main__":
    main()

