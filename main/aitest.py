from ultralytics import YOLO
import cv2
import os
import torch

# MediaPipe imports
import mediapipe as mp
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


def _pose_bbox_from_landmarks(landmarks, w, h, margin=0.05):
    """Compute a loose bbox around pose landmarks (returns None if not enough points)."""
    xs = [lm.x for lm in landmarks.landmark]
    ys = [lm.y for lm in landmarks.landmark]
    if not xs or not ys:
        return None
    x1 = max(0, int((max(min(xs), 0.0) - margin) * w))
    y1 = max(0, int((max(min(ys), 0.0) - margin) * h))
    x2 = min(w - 1, int((min(max(xs), 1.0) + margin) * w))
    y2 = min(h - 1, int((min(max(ys), 1.0) + margin) * h))
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2, y2)


def video_replay(cap, model, model2, pose=None, draw_pose_bbox=True):
    """
    Uses OpenCV to show frame-by-frame video with YOLO detections.
    If 'pose' is provided (MediaPipe Pose), also overlays a skeleton (and optional bbox).
    """
    # Move models to GPU once (not inside the loop)
    if torch.cuda.is_available():
        model.to('cuda')
        model2.to('cuda')

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # your video is portrait — keep your rotation
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # --- YOLO detections ---
        results = model(frame, imgsz=1280, conf=0.33)
        results2 = model2(frame, imgsz=1280, conf=0.33)

        annotated_frame = results[0].plot()

        # Model 1 (e.g., basketball/hoop)
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])
            if label == "Basketball":
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"{label} {conf:.2f}", (x1, max(0, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Model 2 (e.g., players/hoop, etc.)
        for box in results2[0].boxes:
            cls_id = int(box.cls[0])
            label = model2.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(annotated_frame, f"{label} {conf:.2f}", (x1, min(annotated_frame.shape[0]-5, y2 + 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # --- MediaPipe Pose (single most-prominent person) ---
        if pose is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)

            if res.pose_landmarks:
                # draw skeleton
                mp_drawing.draw_landmarks(
                    annotated_frame,
                    res.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style()
                )

                # optional bbox around the person
                if draw_pose_bbox:
                    h, w = annotated_frame.shape[:2]
                    bb = _pose_bbox_from_landmarks(res.pose_landmarks, w, h, margin=0.03)
                    if bb:
                        x1, y1, x2, y2 = bb
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                        cv2.putText(annotated_frame, "Person (MP Pose)", (x1, max(0, y1 - 8)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

        # Show combined result
        cv2.imshow("Detections + MediaPipe Pose", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def frame_saver(cap, model, save_folder, pose=None, draw_pose_bbox=True):
    """
    Generates frames with YOLO (and optional MediaPipe Pose) overlays and saves to disk.
    """
    os.makedirs(save_folder, exist_ok=True)
    frame_count = 0

    #  Move model once
    if torch.cuda.is_available():
        model.to('cuda')

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        results = model(frame, imgsz=1280, conf=0.33)
        annotated_frame = results[0].plot()

        #  Pose overlay (optional)
        if pose is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)
            if res.pose_landmarks:
                mp_drawing.draw_landmarks(
                    annotated_frame,
                    res.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style()
                )
                if draw_pose_bbox:
                    h, w = annotated_frame.shape[:2]
                    bb = _pose_bbox_from_landmarks(res.pose_landmarks, w, h, margin=0.03)
                    if bb:
                        x1, y1, x2, y2 = bb
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

        # Save
        save_path = os.path.join(save_folder, f"frame_{frame_count:05d}.jpg")
        cv2.imwrite(save_path, annotated_frame)
        frame_count += 1

        cv2.imshow("Basketball Detection + MP Pose", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    print("CUDA available:", torch.cuda.is_available())

    # YOLO models
    model = YOLO("models/hoop.pt")
    model2 = YOLO("models/best.pt")

    #  Create MediaPipe Pose once (single-person, fast)
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,          # 0 = fastest, 2 = most accurate
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    video_path = "./test_videos/test_vid.mov"
    save_folder = "./annotated_frames"

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Failed to open video.")

    # Show live replay with YOLO + MediaPipe
    video_replay(cap, model, model2, pose=pose)

    # Or save frames:
    # cap = cv2.VideoCapture(video_path)
    # frame_saver(cap, model, save_folder, pose=pose)
