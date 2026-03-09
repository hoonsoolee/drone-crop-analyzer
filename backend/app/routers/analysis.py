"""
작물 분석 라우터
면적 산출 + 생육 진단
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.config import settings
from app.models.schemas import AnalysisRequest, CropAnalysisResult, ImageType
from app.services.crop_detector import CropDetector
from app.services.spectral_processor import SpectralProcessor
from app.services.area_calculator import AreaCalculator
from app.services.growth_analyzer import GrowthAnalyzer
from app.routers.upload import sessions
from app.routers.stitching import stitch_results

router = APIRouter(prefix="/analysis", tags=["analysis"])

detector = CropDetector()
spectral = SpectralProcessor()
calculator = AreaCalculator(gsd_cm=2.74)
growth = GrowthAnalyzer()

analysis_results: dict[str, dict] = {}


def _run_analysis(session_id: str, crop_type: str, image_type: str, custom_threshold: float):
    """백그라운드 분석 작업"""
    try:
        output_dir = settings.OUTPUT_DIR / session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        analysis_results[session_id] = {"status": "processing"}

        stitch_info = stitch_results.get(session_id, {})
        stitched_path = stitch_info.get("stitched_path")
        w = stitch_info.get("width", 0)
        h = stitch_info.get("height", 0)

        mean_ndvi = mean_ndre = mean_gndvi = mean_savi = rgb_exg = None
        ndvi_image_path = None

        if image_type == ImageType.MULTISPECTRAL or image_type == "multispectral":
            # 밴드 경로 수집
            session_dir = settings.UPLOAD_DIR / session_id
            band_paths_dict = {}
            for band in ["red", "green", "blue", "nir", "rededge"]:
                band_file = output_dir / f"stitched_{band}.tif"
                if band_file.exists():
                    band_paths_dict[band] = band_file

            if band_paths_dict:
                indices = spectral.compute_all_indices(band_paths_dict, output_dir)

                if "ndvi" in indices:
                    mean_ndvi = indices["ndvi"]["mean"]
                    ndvi_image_path = indices["ndvi"]["path"]
                    ndvi_array = indices["ndvi"]["array"]
                    detect_result = detector.detect_multispectral(
                        ndvi_array, (h, w), crop_type, output_dir, custom_threshold
                    )
                if "ndre" in indices:
                    mean_ndre = indices["ndre"]["mean"]
                if "gndvi" in indices:
                    mean_gndvi = indices["gndvi"]["mean"]
                if "savi" in indices:
                    mean_savi = indices["savi"]["mean"]
            else:
                analysis_results[session_id] = {"status": "failed", "message": "밴드 파일을 찾을 수 없습니다"}
                return

        else:  # RGB
            if not stitched_path or not Path(stitched_path).exists():
                analysis_results[session_id] = {"status": "failed", "message": "정합된 이미지가 없습니다. 먼저 정합을 수행하세요."}
                return

            detect_result = detector.detect_rgb(
                Path(stitched_path), crop_type, output_dir, custom_threshold
            )

            # RGB ExG 계산
            import cv2, numpy as np
            img = cv2.imread(stitched_path)
            if img is not None:
                b = img[:, :, 0].astype(np.float32)
                g = img[:, :, 1].astype(np.float32)
                r = img[:, :, 2].astype(np.float32)
                total = r + g + b + 1e-8
                exg = (2 * g / total - r / total - b / total)
                # 식물로 감지된 픽셀에서만 ExG 평균
                mask = cv2.imread(str(output_dir / "crop_mask.png"), cv2.IMREAD_GRAYSCALE)
                if mask is not None:
                    plant_pixels = exg[mask > 0]
                    rgb_exg = float(plant_pixels.mean()) if len(plant_pixels) > 0 else float(exg.mean())
                else:
                    rgb_exg = float(exg.mean())

        if not detect_result.get("success"):
            analysis_results[session_id] = {"status": "failed", "message": detect_result.get("message", "감지 실패")}
            return

        # 면적 계산
        area_result = calculator.calculate(
            detect_result["crop_pixels"],
            detect_result["total_pixels"],
            w, h,
        )

        # 생육 진단
        growth_result = growth.analyze(
            crop_type,
            mean_ndvi=mean_ndvi,
            mean_ndre=mean_ndre,
            mean_gndvi=mean_gndvi,
            mean_savi=mean_savi,
            rgb_exg=rgb_exg,
        )

        analysis_results[session_id] = {
            "status": "completed",
            "crop_type": crop_type,
            "area": area_result,
            "growth": growth_result,
            "paths": {
                "mask": detect_result.get("mask_path"),
                "overlay": detect_result.get("overlay_path"),
                "ndvi": ndvi_image_path,
            },
            "indices": {
                "ndvi": mean_ndvi,
                "ndre": mean_ndre,
                "gndvi": mean_gndvi,
                "savi": mean_savi,
                "rgb_exg": rgb_exg,
            },
        }

    except Exception as e:
        import traceback
        analysis_results[session_id] = {"status": "failed", "message": f"{e}\n{traceback.format_exc()}"}


@router.post("/", response_model=CropAnalysisResult)
async def start_analysis(req: AnalysisRequest, background_tasks: BackgroundTasks):
    """작물 면적 및 생육 분석 시작"""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    analysis_results[req.session_id] = {"status": "queued"}
    background_tasks.add_task(
        _run_analysis,
        req.session_id,
        req.crop_type.value,
        req.image_type.value,
        req.custom_threshold,
    )

    return CropAnalysisResult(
        session_id=req.session_id,
        crop_type=req.crop_type.value,
        total_area_m2=0,
        total_area_ha=0,
        crop_coverage_percent=0,
        pixel_count=0,
        total_pixels=0,
        growth_status="분석 중...",
        growth_score=0,
    )


@router.get("/{session_id}/status", response_model=CropAnalysisResult)
async def get_analysis_status(session_id: str):
    """분석 결과 조회"""
    result = analysis_results.get(session_id, {})
    status = result.get("status", "not_started")

    if status == "completed":
        area = result["area"]
        growth_r = result["growth"]
        paths = result.get("paths", {})
        indices = result.get("indices", {})

        return CropAnalysisResult(
            session_id=session_id,
            crop_type=result["crop_type"],
            total_area_m2=area["crop_area_m2"],
            total_area_ha=area["crop_area_ha"],
            crop_coverage_percent=area["coverage_percent"],
            pixel_count=area["pixel_count"],
            total_pixels=area["total_pixels"],
            mean_ndvi=indices.get("ndvi"),
            mean_ndre=indices.get("ndre"),
            mean_gndvi=indices.get("gndvi"),
            mean_savi=indices.get("savi"),
            growth_status=growth_r["growth_status"],
            growth_score=growth_r["growth_score"],
            recommendations=growth_r["recommendations"],
            mask_image_path=paths.get("mask"),
            ndvi_image_path=paths.get("ndvi"),
            overlay_image_path=paths.get("overlay"),
        )

    return CropAnalysisResult(
        session_id=session_id,
        crop_type="",
        total_area_m2=0,
        total_area_ha=0,
        crop_coverage_percent=0,
        pixel_count=0,
        total_pixels=0,
        growth_status=status,
        growth_score=0,
        recommendations=[result.get("message", "")] if result.get("message") else [],
    )


@router.get("/{session_id}/image/{image_type}")
async def get_result_image(session_id: str, image_type: str):
    """결과 이미지 반환 (mask/overlay/ndvi)"""
    result = analysis_results.get(session_id, {})
    if result.get("status") != "completed":
        raise HTTPException(status_code=404, detail="분석 완료된 결과가 없습니다")

    paths = result.get("paths", {})
    path = paths.get(image_type)
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail=f"{image_type} 이미지를 찾을 수 없습니다")
    return FileResponse(path)
