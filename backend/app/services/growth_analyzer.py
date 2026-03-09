"""
작물 생육 진단 서비스
식생 지수 기반 생육 상태 등급화 및 처방 제안
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GrowthThresholds:
    ndvi_excellent: float
    ndvi_good: float
    ndvi_caution: float
    ndre_excellent: Optional[float] = None
    ndre_good: Optional[float] = None
    description: str = ""


# 작물별 생육 기준 NDVI/NDRE 임계값
CROP_THRESHOLDS = {
    "cabbage": GrowthThresholds(
        ndvi_excellent=0.65, ndvi_good=0.45, ndvi_caution=0.25,
        ndre_excellent=0.35, ndre_good=0.20,
        description="배추"
    ),
    "onion": GrowthThresholds(
        ndvi_excellent=0.60, ndvi_good=0.40, ndvi_caution=0.20,
        ndre_excellent=0.30, ndre_good=0.18,
        description="양파"
    ),
    "garlic": GrowthThresholds(
        ndvi_excellent=0.62, ndvi_good=0.42, ndvi_caution=0.22,
        ndre_excellent=0.32, ndre_good=0.19,
        description="마늘"
    ),
    "pepper": GrowthThresholds(
        ndvi_excellent=0.60, ndvi_good=0.40, ndvi_caution=0.20,
        description="고추"
    ),
    "potato": GrowthThresholds(
        ndvi_excellent=0.65, ndvi_good=0.45, ndvi_caution=0.25,
        description="감자"
    ),
    "radish": GrowthThresholds(
        ndvi_excellent=0.60, ndvi_good=0.40, ndvi_caution=0.20,
        description="무"
    ),
    "lettuce": GrowthThresholds(
        ndvi_excellent=0.70, ndvi_good=0.50, ndvi_caution=0.30,
        description="상추"
    ),
    "spinach": GrowthThresholds(
        ndvi_excellent=0.68, ndvi_good=0.48, ndvi_caution=0.28,
        description="시금치"
    ),
    "sweet_potato": GrowthThresholds(
        ndvi_excellent=0.62, ndvi_good=0.42, ndvi_caution=0.22,
        description="고구마"
    ),
    "custom": GrowthThresholds(
        ndvi_excellent=0.60, ndvi_good=0.40, ndvi_caution=0.20,
        description="작물"
    ),
}

GROWTH_RECOMMENDATIONS = {
    "excellent": [
        "현재 생육 상태가 매우 양호합니다.",
        "현재 관개 및 시비 체계를 유지하세요.",
        "병해충 예방적 방제를 정기적으로 실시하세요.",
    ],
    "good": [
        "전반적으로 양호한 생육 상태입니다.",
        "질소 비료를 추가 시비하여 생육을 촉진할 수 있습니다.",
        "관개 일정을 점검하여 토양 수분을 적정 수준으로 유지하세요.",
    ],
    "caution": [
        "생육 부진 구역이 감지되었습니다. 현장 확인이 필요합니다.",
        "토양 검사를 실시하여 영양 결핍 여부를 확인하세요.",
        "관개 시스템 점검 및 수분 공급량을 조절하세요.",
        "병해충 피해 여부를 확인하고 필요시 방제를 실시하세요.",
    ],
    "poor": [
        "심각한 생육 이상이 감지되었습니다. 즉시 현장 확인이 필요합니다.",
        "토양 pH, EC 및 주요 영양소(N, P, K) 분석을 실시하세요.",
        "관수량 및 배수 상태를 긴급 점검하세요.",
        "병해(탄저병, 역병 등) 또는 충해(진딧물, 응애 등) 피해를 확인하세요.",
        "농업기술센터 전문가 상담을 권장합니다.",
    ],
}


class GrowthAnalyzer:
    def analyze(
        self,
        crop_type: str,
        mean_ndvi: Optional[float] = None,
        mean_ndre: Optional[float] = None,
        mean_gndvi: Optional[float] = None,
        mean_savi: Optional[float] = None,
        rgb_exg: Optional[float] = None,  # RGB 전용 ExG 지수
    ) -> dict:
        """
        식생 지수 기반 생육 상태 진단
        Returns: status, score(0-100), recommendations
        """
        thresholds = CROP_THRESHOLDS.get(crop_type, CROP_THRESHOLDS["custom"])
        crop_name = thresholds.description

        # 주 지수 선택 (NDVI > NDRE > ExG 순서)
        primary_index = None
        primary_name = ""
        if mean_ndvi is not None:
            primary_index = mean_ndvi
            primary_name = "NDVI"
        elif rgb_exg is not None:
            # RGB ExG를 NDVI 범위로 스케일링 (약 -0.3~0.3 → -1~1)
            primary_index = float(np.clip(rgb_exg * 2, -1, 1)) if rgb_exg is not None else None
            primary_name = "ExG(RGB)"

        if primary_index is None:
            return {
                "growth_status": "분석 불가",
                "growth_score": 0,
                "recommendations": ["식생 지수를 계산할 수 없습니다. 이미지 품질을 확인하세요."],
                "details": {},
            }

        # NDVI 기반 등급 판정
        if primary_index >= thresholds.ndvi_excellent:
            status = "우수"
            status_en = "excellent"
            base_score = 90
            score = min(100, base_score + (primary_index - thresholds.ndvi_excellent) * 50)
        elif primary_index >= thresholds.ndvi_good:
            status = "양호"
            status_en = "good"
            range_size = thresholds.ndvi_excellent - thresholds.ndvi_good
            progress = (primary_index - thresholds.ndvi_good) / (range_size + 1e-8)
            score = 70 + progress * 20
        elif primary_index >= thresholds.ndvi_caution:
            status = "주의"
            status_en = "caution"
            range_size = thresholds.ndvi_good - thresholds.ndvi_caution
            progress = (primary_index - thresholds.ndvi_caution) / (range_size + 1e-8)
            score = 40 + progress * 30
        else:
            status = "불량"
            status_en = "poor"
            score = max(0, primary_index / (thresholds.ndvi_caution + 1e-8) * 40)

        # NDRE 보정 (멀티스펙트럴 전용)
        if mean_ndre is not None and thresholds.ndre_good is not None:
            if mean_ndre >= thresholds.ndre_excellent:
                score = min(100, score + 5)
            elif mean_ndre < thresholds.ndre_good:
                score = max(0, score - 10)
                if status == "우수":
                    status = "양호"
                    status_en = "good"

        recommendations = GROWTH_RECOMMENDATIONS.get(status_en, [])

        return {
            "growth_status": status,
            "growth_score": round(float(score), 1),
            "recommendations": recommendations,
            "details": {
                "primary_index": primary_name,
                "primary_value": round(primary_index, 4),
                "crop_name": crop_name,
                "ndvi_threshold_excellent": thresholds.ndvi_excellent,
                "ndvi_threshold_good": thresholds.ndvi_good,
                "ndvi_threshold_caution": thresholds.ndvi_caution,
            },
        }


# numpy import (GrowthAnalyzer.analyze에서 사용)
import numpy as np
