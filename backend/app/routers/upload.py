"""
이미지 업로드 라우터
드론 이미지 파일 업로드 및 세션 관리
"""
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.schemas import ImageType, SessionInfo

router = APIRouter(prefix="/upload", tags=["upload"])

# 세션 메타데이터 인메모리 저장 (실제 서비스에서는 DB 사용)
sessions: dict[str, dict] = {}


@router.post("/session", response_model=SessionInfo)
async def create_session(image_type: ImageType = Form(default=ImageType.RGB)):
    """새 업로드 세션 생성"""
    session_id = str(uuid.uuid4())[:8]
    session_dir = settings.UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    sessions[session_id] = {
        "session_id": session_id,
        "image_type": image_type,
        "image_count": 0,
        "created_at": datetime.now().isoformat(),
        "status": "uploading",
        "files": [],
    }

    return SessionInfo(
        session_id=session_id,
        image_count=0,
        image_type=image_type,
        created_at=sessions[session_id]["created_at"],
        status="uploading",
    )


@router.post("/{session_id}/images")
async def upload_images(
    session_id: str,
    files: list[UploadFile] = File(...),
    band: str = Form(default="rgb"),  # rgb, red, green, blue, nir, rededge
):
    """이미지 파일 업로드 (다중 파일 지원)"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    session_dir = settings.UPLOAD_DIR / session_id
    band_dir = session_dir / band
    band_dir.mkdir(parents=True, exist_ok=True)

    uploaded = []
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식: {ext}. 허용: {settings.ALLOWED_EXTENSIONS}",
            )

        dest = band_dir / file.filename
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)

        sessions[session_id]["files"].append(str(dest))
        sessions[session_id]["image_count"] += 1
        uploaded.append(file.filename)

    sessions[session_id]["status"] = "uploaded"

    return {"session_id": session_id, "uploaded": uploaded, "total": sessions[session_id]["image_count"]}


@router.get("/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """세션 정보 조회"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    s = sessions[session_id]
    return SessionInfo(
        session_id=session_id,
        image_count=s["image_count"],
        image_type=s["image_type"],
        created_at=s["created_at"],
        status=s["status"],
    )


@router.get("/")
async def list_sessions():
    """전체 세션 목록"""
    return [
        {
            "session_id": sid,
            "image_count": s["image_count"],
            "image_type": s["image_type"],
            "created_at": s["created_at"],
            "status": s["status"],
        }
        for sid, s in sessions.items()
    ]
