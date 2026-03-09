"""
작물 감지 및 마스크 생성 서비스
RGB: 색상 기반 (HSV) + ExG 식생 지수
멀티스펙트럴: NDVI 임계값 기반
"""
import cv2
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 작물별 HSV 색상 범위 (BGR→HSV 변환 후 적용)
CROP_HSV_RANGES = {
    "cabbage": [  # 배추: 청록~연녹색
        {"lower": np.array([35, 40, 40]), "upper": np.array([85, 255, 255])},
    ],
    "onion": [   # 양파 (녹색 줄기)
        {"lower": np.array([30, 30, 30]), "upper": np.array([90, 255, 200])},
    ],
    "garlic": [  # 마늘 (짙은 녹색)
        {"lower": np.array([35, 50, 30]), "upper": np.array([80, 255, 180])},
    ],
    "pepper": [  # 고추
        {"lower": np.array([30, 40, 40]), "upper": np.array([90, 255, 255])},
    ],
    "potato": [  # 감자
        {"lower": np.array([25, 30, 30]), "upper": np.array([85, 255, 200])},
    ],
    "radish": [  # 무
        {"lower": np.array([30, 40, 40]), "upper": np.array([85, 255, 255])},
    ],
    "lettuce": [ # 상추 (밝은 녹색)
        {"lower": np.array([35, 50, 60]), "upper": np.array([85, 255, 255])},
    ],
    "spinach": [ # 시금치 (짙은 녹색)
        {"lower": np.array([35, 60, 30]), "upper": np.array([80, 255, 200])},
    ],
    "sweet_potato": [  # 고구마
        {"lower": np.array([30, 40, 30]), "upper": np.array([90, 255, 220])},
    ],
    "custom": [  # 범용 녹색 식물
        {"lower": np.array([30, 30, 30]), "upper": np.array([90, 255, 255])},
    ],
}

# NDVI 임계값 (멀티스펙트럴)
NDVI_THRESHOLDS = {
    "default": 0.2,
    "cabbage": 0.25,
    "onion": 0.20,
    "garlic": 0.22,
    "pepper": 0.20,
    "potato": 0.20,
    "radish": 0.22,
    "lettuce": 0.25,
    "spinach": 0.28,
    "sweet_potato": 0.20,
    "custom": 0.15,
}


class CropDetector:
    def detect_rgb(
        self,
        image_path: Path,
        crop_type: str,
        output_dir: Path,
        custom_threshold: float = None,
    ) -> dict:
        """RGB 이미지에서 작물 마스크 생성"""
        img = cv2.imread(str(image_path))
        if img is None:
            return {"success": False, "message": f"이미지 로드 실패: {image_path}"}

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        ranges = CROP_HSV_RANGES.get(crop_type, CROP_HSV_RANGES["custom"])

        # HSV 마스크 합성
        hsv_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for r in ranges:
            m = cv2.inRange(hsv, r["lower"], r["upper"])
            hsv_mask = cv2.bitwise_or(hsv_mask, m)

        # ExG (Excess Green) 식생 지수 마스크
        b = img[:, :, 0].astype(np.float32)
        g = img[:, :, 1].astype(np.float32)
        r = img[:, :, 2].astype(np.float32)
        total = r + g + b + 1e-8
        exg = (2 * g / total - r / total - b / total)

        threshold = custom_threshold if custom_threshold is not None else 0.05
        exg_mask = (exg > threshold).astype(np.uint8) * 255

        # 최종 마스크: HSV AND ExG
        combined_mask = cv2.bitwise_and(hsv_mask, exg_mask)

        # 노이즈 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

        # 마스크 저장
        mask_path = output_dir / "crop_mask.png"
        cv2.imwrite(str(mask_path), combined_mask)

        # 오버레이 이미지 생성
        overlay = img.copy()
        overlay[combined_mask == 0] = (overlay[combined_mask == 0] * 0.3).astype(np.uint8)
        overlay_path = output_dir / "crop_overlay.jpg"
        cv2.imwrite(str(overlay_path), overlay)

        crop_pixels = int(np.sum(combined_mask > 0))
        total_pixels = combined_mask.size

        return {
            "success": True,
            "mask_path": str(mask_path),
            "overlay_path": str(overlay_path),
            "crop_pixels": crop_pixels,
            "total_pixels": total_pixels,
        }

    def detect_multispectral(
        self,
        ndvi_array: np.ndarray,
        image_shape: tuple,
        crop_type: str,
        output_dir: Path,
        custom_threshold: float = None,
    ) -> dict:
        """NDVI 배열 기반 작물 마스크 생성"""
        threshold = custom_threshold if custom_threshold is not None else \
            NDVI_THRESHOLDS.get(crop_type, NDVI_THRESHOLDS["default"])

        # NDVI 임계값 마스크
        mask = (ndvi_array > threshold).astype(np.uint8) * 255

        # 노이즈 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        mask_path = output_dir / "crop_mask_ndvi.png"
        cv2.imwrite(str(mask_path), mask)

        crop_pixels = int(np.sum(mask > 0))
        total_pixels = mask.size

        return {
            "success": True,
            "mask_path": str(mask_path),
            "overlay_path": None,
            "crop_pixels": crop_pixels,
            "total_pixels": total_pixels,
            "ndvi_threshold": threshold,
        }
