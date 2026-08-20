from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pathlib import Path
from app.api.schemas.video import VideoUploadResponse
from app.storage import storage_manager
from app.validation.video_validator import video_validator
from app.context.context_detector import context_detector
from app.config import MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS

router = APIRouter(prefix="/api/videos", tags=["Videos"])

@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing in upload request.")
        
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    content = await file.read()
    file_size_bytes = len(content)
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    
    if file_size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({file_size_bytes / (1024*1024):.1f}MB) exceeds max limit of {MAX_FILE_SIZE_MB}MB."
        )

    # Privacy-First: Save to isolated temporary storage
    video_id, saved_path = storage_manager.save_temp_video(file.filename, content)

    # Run suitability validation & automatic context detection
    try:
        metadata, suitability = video_validator.validate_video(saved_path, file.filename, file_size_bytes)
        detected_context = context_detector.detect_context(saved_path, metadata)
    except Exception as e:
        # Cleanup temporary video if validation crashes
        storage_manager.cleanup_temp_video(video_id)
        raise HTTPException(
            status_code=422,
            detail=f"Failed to process video metadata: {str(e)}"
        )

    return VideoUploadResponse(
        video_id=video_id,
        metadata=metadata,
        suitability=suitability,
        detected_context=detected_context
    )

@router.get("/{video_id}")
def get_video_info(video_id: str):
    path = storage_manager.get_raw_video_path(video_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Video file not found.")
    return {"video_id": video_id, "filename": path.name, "size_bytes": path.stat().st_size}
