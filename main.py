import uuid
import aiofiles
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database import init_db, get_async_session
from models import Detection
from schemas import TaskResponse, DetectionResponse
from tasks import broker, process_video_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.DETECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    await init_db()
    await broker.startup()
    yield
    await broker.shutdown()


app = FastAPI(title=settings.APP_TITLE, lifespan=lifespan)

app.mount("/media", StaticFiles(directory=settings.BASE_DIR / "media"), name="media")


@app.post("/detect/video", response_model=TaskResponse)
async def process_video(file: UploadFile = File(...)):
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Invalid video format")

    temp_filename = f"temp_{uuid.uuid4()}{Path(file.filename).suffix}"
    temp_video_path = settings.BASE_DIR / temp_filename

    async with aiofiles.open(temp_video_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    task = await process_video_task.kiq(str(temp_video_path))

    return TaskResponse(
        task_id=task.task_id,
        status="processing",
        message="Video uploaded and queued for processing"
    )


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    is_ready = await broker.result_backend.is_result_ready(task_id)
    if not is_ready:
        return TaskResponse(
            task_id=task_id, 
            status="pending", 
            message="Task is still processing or not found"
        )
    
    task_result = await broker.result_backend.get_result(task_id)
    if task_result.is_err:
        return TaskResponse(
            task_id=task_id, 
            status="error", 
            message=str(task_result.error)
        )

    return TaskResponse(
        task_id=task_id, 
        status="completed", 
        message=f"Processed frames: {task_result.return_value.get('saved_frames', 0)}"
    )


@app.get("/detections", response_model=List[DetectionResponse])
async def get_detections(
    limit: int = 20, 
    offset: int = 0, 
    db: AsyncSession = Depends(get_async_session)
):
    query = select(Detection).order_by(Detection.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
