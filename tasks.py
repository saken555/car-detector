import os
import cv2
from typing import Optional
from ultralytics import YOLO
from taskiq import TaskiqEvents, Context, TaskiqDepends
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

from config import settings
from database import AsyncSessionLocal
from models import Detection


redis_result_backend = RedisAsyncResultBackend(redis_url=settings.redis_url)
broker = ListQueueBroker(url=settings.redis_url).with_result_backend(redis_result_backend)

model: Optional[YOLO] = None


@broker.on_event(TaskiqEvents.WORKER_START)
def startup_worker() -> None:
    global model
    settings.DETECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    model = YOLO(settings.YOLO_MODEL_PATH)


@broker.task
async def process_video_task(video_path: str, context: Context = TaskiqDepends()) -> dict:
    task_id = context.message.task_id
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        return {"status": "error", "message": f"Cannot open video"}

    frame_idx = 0
    saved_count = 0

    try:
        async with AsyncSessionLocal() as session:
            while cap.isOpened():
                if saved_count >= settings.MAX_SAVED_FRAMES:
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                if frame_idx % settings.FRAME_SKIP != 0:
                    continue

                results = model(frame, conf=settings.MIN_CONF, verbose=False)[0]

                car_boxes = [
                    box for box in results.boxes
                    if int(box.cls[0]) in settings.TARGET_CLASSES
                ]

                if car_boxes:
                    cars_count = len(car_boxes)
                    max_conf = max(float(box.conf[0]) for box in car_boxes)

                    annotated_frame = results.plot()

                    file_name = f"{task_id}_frame_{frame_idx}.jpg"
                    save_path = settings.DETECTIONS_DIR / file_name
                    cv2.imwrite(str(save_path), annotated_frame)

                    detection = Detection(
                        task_id=task_id,
                        frame_number=frame_idx,
                        confidence=max_conf,
                        cars_count=cars_count,
                        image_path=f"/media/detections/{file_name}"
                    )
                    session.add(detection)
                    saved_count += 1

            await session.commit()
    finally:
        cap.release()
        if os.path.exists(video_path):
            os.remove(video_path)

    return {"status": "completed", "saved_frames": saved_count, "task_id": task_id}
