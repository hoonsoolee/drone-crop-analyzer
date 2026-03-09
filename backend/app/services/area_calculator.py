"""
면적 산출 서비스
픽셀 수 → 실제 면적(m², ha) 변환
GSD(Ground Sampling Distance) 기반 계산
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)

# 드론 고도별 대략적인 GSD (cm/pixel) - 기본값
# 실제로는 EXIF/카메라 메타데이터에서 읽어야 함
DEFAULT_GSD_TABLE = {
    # (고도 m): GSD cm/pixel (DJI Phantom 4 Pro 기준)
    30: 0.83,
    50: 1.38,
    80: 2.21,
    100: 2.74,
    120: 3.29,
    150: 4.11,
}
DEFAULT_GSD_CM = 2.74  # 100m 고도 기본값


class AreaCalculator:
    def __init__(self, gsd_cm: float = DEFAULT_GSD_CM):
        """
        gsd_cm: Ground Sampling Distance (cm/pixel)
        - DJI Phantom 4 Pro @ 100m → ~2.74 cm/pixel
        - DJI Mini 3 @ 100m → ~3.7 cm/pixel
        - MicaSense RedEdge @ 120m → ~8 cm/pixel
        """
        self.gsd_cm = gsd_cm
        self.gsd_m = gsd_cm / 100.0
        self.pixel_area_m2 = self.gsd_m ** 2

    def pixels_to_area(self, pixel_count: int) -> dict:
        """픽셀 수를 실제 면적으로 변환"""
        area_m2 = pixel_count * self.pixel_area_m2
        area_ha = area_m2 / 10000.0
        area_pyeong = area_m2 / 3.3058  # 평 (한국 단위)

        return {
            "area_m2": round(area_m2, 2),
            "area_ha": round(area_ha, 4),
            "area_pyeong": round(area_pyeong, 1),
        }

    def calculate(
        self,
        crop_pixels: int,
        total_pixels: int,
        image_width: int = None,
        image_height: int = None,
    ) -> dict:
        """작물 면적 계산 결과 반환"""
        area = self.pixels_to_area(crop_pixels)
        total_area = self.pixels_to_area(total_pixels)

        coverage_pct = (crop_pixels / total_pixels * 100) if total_pixels > 0 else 0

        return {
            "crop_area_m2": area["area_m2"],
            "crop_area_ha": area["area_ha"],
            "crop_area_pyeong": area["area_pyeong"],
            "total_area_m2": total_area["area_m2"],
            "total_area_ha": total_area["area_ha"],
            "coverage_percent": round(coverage_pct, 2),
            "pixel_count": crop_pixels,
            "total_pixels": total_pixels,
            "gsd_cm": self.gsd_cm,
        }

    @staticmethod
    def estimate_gsd_from_altitude(altitude_m: float, sensor_width_mm: float = 13.2,
                                   focal_length_mm: float = 8.8, image_width_px: int = 5472) -> float:
        """고도, 센서 크기, 초점 거리로 GSD 추정"""
        gsd_cm = (altitude_m * sensor_width_mm / focal_length_mm / image_width_px) * 100
        return round(gsd_cm, 3)
