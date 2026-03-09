from pydantic import BaseModel
from typing import Optional
from enum import Enum


class CropType(str, Enum):
    CABBAGE = "cabbage"       # 배추
    ONION = "onion"           # 양파
    GARLIC = "garlic"         # 마늘
    PEPPER = "pepper"         # 고추
    POTATO = "potato"         # 감자
    SWEET_POTATO = "sweet_potato"  # 고구마
    RADISH = "radish"         # 무
    LETTUCE = "lettuce"       # 상추
    SPINACH = "spinach"       # 시금치
    CUSTOM = "custom"         # 사용자 정의


class ImageType(str, Enum):
    RGB = "rgb"
    MULTISPECTRAL = "multispectral"


class StitchingMethod(str, Enum):
    PANORAMA = "panorama"
    SCAN = "scan"


class StitchingRequest(BaseModel):
    session_id: str
    image_type: ImageType = ImageType.RGB
    method: StitchingMethod = StitchingMethod.SCAN


class StitchingResult(BaseModel):
    session_id: str
    status: str
    stitched_image_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    message: str = ""


class AnalysisRequest(BaseModel):
    session_id: str
    crop_type: CropType
    image_type: ImageType = ImageType.RGB
    custom_threshold: Optional[float] = None  # NDVI 또는 색상 임계값


class CropAnalysisResult(BaseModel):
    session_id: str
    crop_type: str
    total_area_m2: float
    total_area_ha: float
    crop_coverage_percent: float
    pixel_count: int
    total_pixels: int

    # 성장 진단 지표
    mean_ndvi: Optional[float] = None
    mean_ndre: Optional[float] = None
    mean_gndvi: Optional[float] = None
    mean_savi: Optional[float] = None
    growth_status: str = ""     # 우수 / 양호 / 주의 / 불량
    growth_score: float = 0.0   # 0~100
    recommendations: list[str] = []

    # 결과 이미지 경로
    mask_image_path: Optional[str] = None
    ndvi_image_path: Optional[str] = None
    overlay_image_path: Optional[str] = None


class SessionInfo(BaseModel):
    session_id: str
    image_count: int
    image_type: ImageType
    created_at: str
    status: str
