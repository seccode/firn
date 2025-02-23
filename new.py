import cv2
import numpy as np
import subprocess

def compress_3pass(input_path, output_path):
    """
    Three-pass compression:
      - 1st pass: B channel = original R, for frames [0..N-1].
      - 2nd pass: B channel = original G, for frames [N..2N-1].
      - 3rd pass: B channel = original B, for frames [2N..3N-1].
    Produces 3x as many frames as the input.
    """

    # First, open the input once to get properties
    cap_probe = cv2.VideoCapture(input_path)
    if not cap_probe.isOpened():
        raise IOError(f"Cannot open input video: {input_path}")

    width  = int(cap_probe.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap_probe.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap_probe.get(cv2.CAP_PROP_FPS)

    # Count how many frames (N) are in the input so we know the total
    # This can be done by reading or using CAP_PROP_FRAME_COUNT (less reliable
    # for some formats, but let's try).
    total_frames = int(cap_probe.get(cv2.CAP_PROP_FRAME_COUNT))
    cap_probe.release()

    if total_frames <= 0:
        # Fallback: count manually if needed
        # but for simplicity let's just assume CAP_PROP_FRAME_COUNT works.
        raise ValueError("Could not determine number of frames (or zero frames).")

    # Prepare the output writer: 3N frames, but we just keep the same fps,
    # so the compressed video will be 3x longer in duration.
    fourcc = cv2.VideoWriter_fourcc(*"FFV1")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        raise IOError(f"Cannot open output video for writing: {output_path}")

    print(f"[compress_3pass] Input has {total_frames} frames. Producing 3x = {3*total_frames} frames.")

    # Helper function to make a blank frame with only the B channel set
    def make_frame_b_channel(h, w, dtype, channel_data):
        # channel_data shape = (h, w), single channel
        # we want a (h, w, 3) with R=G=0, B = channel_data
        out_frame = np.zeros((h, w, 3), dtype=dtype)
        out_frame[..., 2] = channel_data  # B is index 2 in OpenCV's BGR
        return out_frame

    # === PASS #1: B = R ===============================================
    pass1_cap = cv2.VideoCapture(input_path)
    pass1_count = 0
    while True:
        ret, frame_bgr = pass1_cap.read()
        if not ret:
            break
        pass1_count += 1

        # Extract the R channel (index 2 in BGR)
        R_channel = frame_bgr[..., 2]
        # Build new frame with only B=R
        new_frame_bgr = make_frame_b_channel(height, width, frame_bgr.dtype, R_channel)
        out.write(new_frame_bgr)

    pass1_cap.release()
    print(f"[compress_3pass] Pass #1 wrote {pass1_count} frames.")

    # === PASS #2: B = G ===============================================
    pass2_cap = cv2.VideoCapture(input_path)
    pass2_count = 0
    while True:
        ret, frame_bgr = pass2_cap.read()
        if not ret:
            break
        pass2_count += 1

        # G channel is index 1 in BGR
        G_channel = frame_bgr[..., 1]
        new_frame_bgr = make_frame_b_channel(height, width, frame_bgr.dtype, G_channel)
        out.write(new_frame_bgr)

    pass2_cap.release()
    print(f"[compress_3pass] Pass #2 wrote {pass2_count} frames.")

    # === PASS #3: B = B ===============================================
    pass3_cap = cv2.VideoCapture(input_path)
    pass3_count = 0
    while True:
        ret, frame_bgr = pass3_cap.read()
        if not ret:
            break
        pass3_count += 1

        # B channel is index 0 in BGR
        B_channel = frame_bgr[..., 0]
        new_frame_bgr = make_frame_b_channel(height, width, frame_bgr.dtype, B_channel)
        out.write(new_frame_bgr)

    pass3_cap.release()
    print(f"[compress_3pass] Pass #3 wrote {pass3_count} frames.")

    # Clean up
    out.release()
    total_written = pass1_count + pass2_count + pass3_count
    print(f"[compress_3pass] Done. Total frames written = {total_written}.")


def decompress_3pass(compressed_path, output_path):
    """
    Three-pass decompression:
      - The compressed file has 3N frames total.
      - Pass #1: read the first 1/3 (N) frames, extract B => R
      - Pass #2: read the next 1/3 (N) frames, extract B => G
      - Pass #3: read the final 1/3 (N) frames, extract B => B
    Then combine R, G, B into the original N frames and write them out.

    Note: Here we do store N frames worth of data (R, G, B) in memory.
    """
    cap = cv2.VideoCapture(compressed_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open compressed video: {compressed_path}")

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if total_frames % 3 != 0:
        raise ValueError("Compressed video does not have a multiple of 3 frames.")

    N = total_frames // 3
    print(f"[decompress_3pass] Compressed has {total_frames} frames => {N} original frames.")

    # We'll store R, G, B in memory as (N, H, W)
    R_buffer = np.zeros((N, height, width), dtype=np.uint8)
    G_buffer = np.zeros((N, height, width), dtype=np.uint8)
    B_buffer = np.zeros((N, height, width), dtype=np.uint8)

    # === PASS #1: B => R ==========================================
    cap1 = cv2.VideoCapture(compressed_path)
    pass1_count = 0
    while pass1_count < N:
        ret, frame_bgr = cap1.read()
        if not ret:
            break
        # The B channel in BGR is index 0
        B_channel = frame_bgr[..., 0]
        # This was originally the R channel in the uncompressed
        R_buffer[pass1_count] = B_channel
        pass1_count += 1
    cap1.release()
    print(f"[decompress_3pass] Pass #1 read {pass1_count} frames.")

    # === PASS #2: B => G ==========================================
    cap2 = cv2.VideoCapture(compressed_path)
    # Skip first N frames
    for _ in range(N):
        cap2.read()

    pass2_count = 0
    while pass2_count < N:
        ret, frame_bgr = cap2.read()
        if not ret:
            break
        B_channel = frame_bgr[..., 0]
        G_buffer[pass2_count] = B_channel
        pass2_count += 1
    cap2.release()
    print(f"[decompress_3pass] Pass #2 read {pass2_count} frames.")

    # === PASS #3: B => B ==========================================
    cap3 = cv2.VideoCapture(compressed_path)
    # Skip first 2N frames
    for _ in range(2*N):
        cap3.read()

    pass3_count = 0
    while pass3_count < N:
        ret, frame_bgr = cap3.read()
        if not ret:
            break
        B_channel = frame_bgr[..., 0]
        B_buffer[pass3_count] = B_channel
        pass3_count += 1
    cap3.release()
    print(f"[decompress_3pass] Pass #3 read {pass3_count} frames.")

    # Now combine R_buffer, G_buffer, B_buffer into the original frames
    # shape => (N, height, width, 3)
    out_frames = np.zeros((N, height, width, 3), dtype=np.uint8)
    out_frames[..., 2] = R_buffer  # R
    out_frames[..., 1] = G_buffer  # G
    out_frames[..., 0] = B_buffer  # B

    # Write the decompressed video
    fourcc = 0
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    for i in range(N):
        out.write(out_frames[i])
    out.release()

    print(f"[decompress_3pass] Decompressed to {N} frames and wrote {output_path}.")


def main():
    input_video      = "input.mp4"
    compressed_video = "output.avi"
    decompressed_video = "restored.avi"

    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", input_video,
        "-c:v", "libaom-av1",
        "-crf", "27",
        "-b:v", "0",
        "-cpu-used", "8",
        "out.mp4"
    ])

    compress_3pass(input_video, compressed_video)
    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", compressed_video,
        "-c:v", "libaom-av1",
        "-crf", "27",
        "-b:v", "0",
        "-cpu-used", "8",
        "out.mp4"
    ])

    # 2) Decompress with a 3-pass method -> N frames
    decompress_3pass("out.mp4", decompressed_video)


if __name__ == "__main__":
    main()

