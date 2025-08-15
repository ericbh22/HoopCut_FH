# scrapes the frames so we can use them to train ultralytics model
import cv2
import os

def extract_frames(video_path, output_folder, every_n_frames=5):
    """
    Function Description: takes every n frames and saves them to use for data annotation 
    """
    os.makedirs(output_folder, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    count = 175
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % every_n_frames == 0:
            filename = os.path.join(output_folder, f"frame_{count:05d}.jpg")
            cv2.imwrite(filename, frame)
            count += 1

        frame_idx += 1

    cap.release()
    print(f"Extracted {count} frames.")

if __name__ ==" __main__":  
    extract_frames("test_videos/full_game_longer.mov", "dataset/frames2/", every_n_frames=20) 
