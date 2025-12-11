from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

def run_detection(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            raise RuntimeError("Gagal membuka video")

    fps_real = cap.get(cv2.CAP_PROP_FPS)
    FPS = int(round(fps_real)) if fps_real > 0 else 30

    SKIP = max(1, FPS // 2)   # cek 1 frame per 0.5 detik

    cheat_person_count = 0
    frame_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_id += 1
        if frame_id % SKIP != 0:
            continue

        # resize agar inference cepat
        frame = cv2.resize(frame, (480, 270))

        # YOLO inference
        results = model(frame, imgsz=480, conf=0.6, verbose=False)[0]
        person_count = sum(1 for box in results.boxes if int(box.cls) == 0)

        if person_count > 1:
            cheat_person_count += 1

    cap.release()

    return {
        "banyak_orang_terdeteksi": cheat_person_count,
        "final": "MENCURIGAKAN" if cheat_person_count > 0 else "TIDAK_MENCURIGAKAN"
    }
