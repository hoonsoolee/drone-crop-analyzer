"""
이미지 정합 라우터
업로드된 드론 이미지를 모자이크/정합하여 정사영상 생성
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.config import settings
from app.models.schemas import StitchingRequest, StitchingResult
from app.services.image_stitcher import ImageStitcher
from app.routers.upload import sessions

router = APIRouter(prefix="/stitch", tags=["stitching"])
stitcher = ImageStitcher()

# 정합 결과 저장
stitch_results: dict[str, dict] = {}


def _run_stitching(session_id: str, method: str, image_type: str):
    """백그라운드 정합 작업"""
    try:
        session_dir = settings.UPLOAD_DIR / session_id
        output_dir = settings.OUTPUT_DIR / session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        stitch_results[session_id] = {"status": "processing"}
        sessions[session_id]["status"] = "stitching"

        if image_type == "rgb":
            image_paths = sorted(
                list((session_dir / "rgb").glob("*"))
                + [p for p in session_dir.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
                   and p.is_file()]
            )
            # rgb 하위 폴더가 없을 경우 루트에서 수집
            if not image_paths:
                image_paths = [
                    p for p in session_dir.rglob("*")
                    if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
                ]

            output_path = output_dir / "stitched.jpg"
            result = stitcher.stitch_rgb(image_paths, output_path, mode=method)

            if result["success"]:
                thumb_path = output_dir / "thumb.jpg"
                stitcher.create_thumbnail(output_path, thumb_path)
                stitch_results[session_id] = {
                    "status": "completed",
                    "stitched_path": str(output_path),
                    "thumb_path": str(thumb_path),
                    "width": result["width"],
                    "height": result["height"],
                    "message": result["message"],
                }
                sessions[session_id]["status"] = "stitched"
            else:
                stitch_results[session_id] = {"status": "failed", "message": result["message"]}
                sessions[session_id]["status"] = "error"

        else:  # multispectral
            band_names = ["red", "green", "blue", "nir", "rededge"]
            band_paths = {}
            for band in band_names:
                band_dir = session_dir / band
                if band_dir.exists():
                    band_paths[band] = sorted(band_dir.glob("*"))

            result = stitcher.stitch_multispectral(band_paths, output_dir, mode=method)

            if result["success"]:
                stitch_results[session_id] = {
                    "status": "completed",
                    "band_paths": result.get("band_paths", {}),
                    "stitched_path": result.get("preview_path"),
                    "thumb_path": result.get("preview_path"),
                    "width": result["width"],
                    "height": result["height"],
                    "message": result["message"],
                }
                sessions[session_id]["status"] = "stitched"
            else:
                stitch_results[session_id] = {"status": "failed", "message": result["message"]}
                sessions[session_id]["status"] = "error"

    except Exception as e:
        stitch_results[session_id] = {"status": "failed", "message": str(e)}
        sessions[session_id]["status"] = "error"


@router.post("/", response_model=StitchingResult)
async def start_stitching(req: StitchingRequest, background_tasks: BackgroundTasks):
    """이미지 정합 시작 (비동기)"""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    stitch_results[req.session_id] = {"status": "queued"}
    background_tasks.add_task(
        _run_stitching, req.session_id, req.method.value, req.image_type.value
    )

    return StitchingResult(
        session_id=req.session_id,
        status="queued",
        message="정합 작업이 시작되었습니다",
    )


@router.get("/{session_id}/status", response_model=StitchingResult)
async def get_stitch_status(session_id: str):
    """정합 상태 조회"""
    result = stitch_results.get(session_id, {})
    status = result.get("status", "not_started")

    return StitchingResult(
        session_id=session_id,
        status=status,
        stitched_image_path=result.get("stitched_path"),
        thumbnail_path=result.get("thumb_path"),
        image_width=result.get("width"),
        image_height=result.get("height"),
        message=result.get("message", ""),
    )


@router.get("/{session_id}/image")
async def get_stitched_image(session_id: str):
    """정합된 이미지 반환"""
    result = stitch_results.get(session_id, {})
    if result.get("status") != "completed":
        raise HTTPException(status_code=404, detail="정합 완료된 이미지가 없습니다")
    path = result.get("stitched_path")
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다")
    return FileResponse(path)


@router.get("/{session_id}/thumbnail")
async def get_thumbnail(session_id: str):
    """썸네일 반환"""
    result = stitch_results.get(session_id, {})
    path = result.get("thumb_path")
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="썸네일이 없습니다")
    return FileResponse(path)
