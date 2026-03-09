"""
드론 이미지 정합(Stitching) 서비스
RGB 및 멀티스펙트럴 이미지를 모자이크/정합하여 정사영상 생성
"""
import cv2
import numpy as np
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ImageStitcher:
    def __init__(self):
        self.stitcher_scan = cv2.Stitcher.create(cv2.Stitcher_SCANS)
        self.stitcher_pano = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)

    def stitch_rgb(
        self,
        image_paths: list[Path],
        output_path: Path,
        mode: str = "scan",
    ) -> dict:
        """RGB 이미지 정합"""
        images = []
        for p in image_paths:
            img = cv2.imread(str(p))
            if img is None:
                logger.warning(f"이미지 로드 실패: {p}")
                continue
            images.append(img)

        if len(images) < 2:
            if len(images) == 1:
                # 이미지 1장이면 그대로 저장
                cv2.imwrite(str(output_path), images[0])
                h, w = images[0].shape[:2]
                return {
                    "success": True,
                    "width": w,
                    "height": h,
                    "message": "단일 이미지 (정합 불필요)",
                }
            return {"success": False, "message": "정합할 이미지가 부족합니다 (최소 2장)"}

        stitcher = self.stitcher_scan if mode == "scan" else self.stitcher_pano
        status, stitched = stitcher.stitch(images)

        if status == cv2.Stitcher_OK:
            cv2.imwrite(str(output_path), stitched)
            h, w = stitched.shape[:2]
            logger.info(f"정합 완료: {output_path} ({w}x{h})")
            return {"success": True, "width": w, "height": h, "message": "정합 성공"}
        else:
            error_map = {
                cv2.Stitcher_ERR_NEED_MORE_IMGS: "이미지 수 부족",
                cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL: "호모그래피 추정 실패 (이미지 중복도 확인)",
                cv2.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL: "카메라 파라미터 조정 실패",
            }
            msg = error_map.get(status, f"알 수 없는 오류 (code: {status})")
            logger.error(f"정합 실패: {msg}")
            return {"success": False, "message": msg}

    def stitch_multispectral(
        self,
        band_paths: dict[str, list[Path]],
        output_dir: Path,
        mode: str = "scan",
    ) -> dict:
        """
        멀티스펙트럴 이미지 정합
        band_paths: {'red': [...], 'green': [...], 'blue': [...], 'nir': [...], 'rededge': [...]}
        """
        stitched_bands = {}
        reference_shape = None

        for band_name, paths in band_paths.items():
            if not paths:
                continue

            images = []
            for p in paths:
                img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    # 16-bit TIF 시도
                    img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
                if img is not None:
                    images.append(img)

            if len(images) == 0:
                continue

            if len(images) == 1:
                stitched_bands[band_name] = images[0]
                reference_shape = images[0].shape
                continue

            # 그레이스케일 → BGR 변환 후 정합 (OpenCV Stitcher는 BGR 필요)
            bgr_images = [cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if len(img.shape) == 2 else img
                         for img in images]

            stitcher = self.stitcher_scan if mode == "scan" else self.stitcher_pano
            status, stitched_bgr = stitcher.stitch(bgr_images)

            if status == cv2.Stitcher_OK:
                stitched_gray = cv2.cvtColor(stitched_bgr, cv2.COLOR_BGR2GRAY)
                stitched_bands[band_name] = stitched_gray
                reference_shape = stitched_gray.shape
                logger.info(f"밴드 {band_name} 정합 완료")
            else:
                logger.warning(f"밴드 {band_name} 정합 실패 (code: {status}), 첫 번째 이미지 사용")
                stitched_bands[band_name] = images[0]

        if not stitched_bands:
            return {"success": False, "message": "정합된 밴드 없음"}

        # 모든 밴드를 동일 크기로 리사이즈
        if reference_shape:
            h, w = reference_shape
            for band_name in stitched_bands:
                if stitched_bands[band_name].shape[:2] != (h, w):
                    stitched_bands[band_name] = cv2.resize(
                        stitched_bands[band_name], (w, h)
                    )

        # 각 밴드 저장
        saved_paths = {}
        for band_name, band_img in stitched_bands.items():
            out_path = output_dir / f"stitched_{band_name}.tif"
            cv2.imwrite(str(out_path), band_img)
            saved_paths[band_name] = str(out_path)

        # RGB 합성 미리보기 생성
        preview_path = output_dir / "stitched_preview.jpg"
        self._create_preview(stitched_bands, preview_path)

        return {
            "success": True,
            "band_paths": saved_paths,
            "preview_path": str(preview_path),
            "width": reference_shape[1] if reference_shape else 0,
            "height": reference_shape[0] if reference_shape else 0,
            "message": f"{len(stitched_bands)}개 밴드 정합 완료",
        }

    def _create_preview(self, bands: dict, output_path: Path):
        """밴드 데이터로 RGB 미리보기 생성"""
        r = bands.get("red") or bands.get("R")
        g = bands.get("green") or bands.get("G")
        b = bands.get("blue") or bands.get("B")

        if r is None or g is None or b is None:
            available = list(bands.values())
            if len(available) >= 3:
                r, g, b = available[0], available[1], available[2]
            elif len(available) == 1:
                img = available[0]
                preview = cv2.merge([img, img, img])
                cv2.imwrite(str(output_path), preview)
                return
            else:
                return

        def normalize(band):
            band = band.astype(np.float32)
            mn, mx = band.min(), band.max()
            if mx > mn:
                return ((band - mn) / (mx - mn) * 255).astype(np.uint8)
            return np.zeros_like(band, dtype=np.uint8)

        bgr = cv2.merge([normalize(b), normalize(g), normalize(r)])
        cv2.imwrite(str(output_path), bgr)

    def create_thumbnail(self, image_path: Path, thumb_path: Path, max_size: int = 800):
        """썸네일 생성"""
        img = cv2.imread(str(image_path))
        if img is None:
            img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            return False

        h, w = img.shape[:2]
        scale = min(max_size / w, max_size / h, 1.0)
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        cv2.imwrite(str(thumb_path), img)
        return True
