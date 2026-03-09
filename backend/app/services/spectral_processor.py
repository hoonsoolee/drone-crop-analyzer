"""
멀티스펙트럴 지수 계산 서비스
NDVI, NDRE, GNDVI, SAVI, EVI 등 식생 지수 산출
"""
import numpy as np
import cv2
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

EPS = 1e-8  # 0 나눗셈 방지


class SpectralProcessor:
    def load_band(self, path: Path) -> np.ndarray:
        """단일 밴드 이미지 로드 → float32 [0,1] 정규화"""
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"밴드 파일 로드 실패: {path}")
        img = img.astype(np.float32)
        # 16-bit → [0,1] 정규화
        max_val = 65535.0 if img.max() > 255 else 255.0
        return img / max_val

    def ndvi(self, nir: np.ndarray, red: np.ndarray) -> np.ndarray:
        """NDVI = (NIR - Red) / (NIR + Red) → [-1, 1]"""
        denom = nir + red + EPS
        return np.clip((nir - red) / denom, -1, 1)

    def ndre(self, nir: np.ndarray, rededge: np.ndarray) -> np.ndarray:
        """NDRE = (NIR - RedEdge) / (NIR + RedEdge) → [-1, 1]"""
        denom = nir + rededge + EPS
        return np.clip((nir - rededge) / denom, -1, 1)

    def gndvi(self, nir: np.ndarray, green: np.ndarray) -> np.ndarray:
        """GNDVI = (NIR - Green) / (NIR + Green) → [-1, 1]"""
        denom = nir + green + EPS
        return np.clip((nir - green) / denom, -1, 1)

    def savi(self, nir: np.ndarray, red: np.ndarray, L: float = 0.5) -> np.ndarray:
        """SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)"""
        denom = nir + red + L + EPS
        return np.clip(((nir - red) / denom) * (1 + L), -1, 1)

    def evi(
        self,
        nir: np.ndarray,
        red: np.ndarray,
        blue: np.ndarray,
        G: float = 2.5,
        C1: float = 6.0,
        C2: float = 7.5,
        L: float = 1.0,
    ) -> np.ndarray:
        """EVI = G * (NIR - Red) / (NIR + C1*Red - C2*Blue + L)"""
        denom = nir + C1 * red - C2 * blue + L + EPS
        return np.clip(G * (nir - red) / denom, -1, 1)

    def rgb_vegetation_index(self, bgr: np.ndarray) -> np.ndarray:
        """
        RGB 이미지용 식생 지수 (ExG - ExR)
        ExG = 2g - r - b  (g,r,b는 정규화된 채널)
        """
        b = bgr[:, :, 0].astype(np.float32) / 255.0
        g = bgr[:, :, 1].astype(np.float32) / 255.0
        r = bgr[:, :, 2].astype(np.float32) / 255.0

        total = r + g + b + EPS
        r_n, g_n, b_n = r / total, g / total, b / total

        exg = 2 * g_n - r_n - b_n   # Excess Green
        exr = 1.4 * r_n - g_n       # Excess Red
        exgr = exg - exr
        return np.clip(exgr, -1, 1)

    def colorize_index(self, index: np.ndarray, vmin: float = -1, vmax: float = 1) -> np.ndarray:
        """식생 지수를 컬러맵(RdYlGn)으로 시각화 → BGR uint8"""
        normalized = np.clip((index - vmin) / (vmax - vmin + EPS), 0, 1)
        colored = (normalized * 255).astype(np.uint8)
        return cv2.applyColorMap(colored, cv2.COLORMAP_RdYlGn if hasattr(cv2, "COLORMAP_RdYlGn")
                                 else cv2.COLORMAP_JET)

    def compute_all_indices(
        self,
        band_paths: dict[str, Path],
        output_dir: Path,
    ) -> dict:
        """
        사용 가능한 밴드로 모든 지수를 계산하고 저장
        band_paths keys: 'red','green','blue','nir','rededge'
        """
        bands = {}
        for name, path in band_paths.items():
            if path and Path(path).exists():
                try:
                    bands[name] = self.load_band(Path(path))
                except Exception as e:
                    logger.warning(f"밴드 {name} 로드 실패: {e}")

        results = {}

        if "nir" in bands and "red" in bands:
            ndvi_arr = self.ndvi(bands["nir"], bands["red"])
            ndvi_img = self.colorize_index(ndvi_arr, -1, 1)
            out = output_dir / "ndvi.png"
            cv2.imwrite(str(out), ndvi_img)
            results["ndvi"] = {
                "path": str(out),
                "mean": float(ndvi_arr.mean()),
                "std": float(ndvi_arr.std()),
                "array": ndvi_arr,
            }

        if "nir" in bands and "rededge" in bands:
            ndre_arr = self.ndre(bands["nir"], bands["rededge"])
            ndre_img = self.colorize_index(ndre_arr, -1, 1)
            out = output_dir / "ndre.png"
            cv2.imwrite(str(out), ndre_img)
            results["ndre"] = {
                "path": str(out),
                "mean": float(ndre_arr.mean()),
                "array": ndre_arr,
            }

        if "nir" in bands and "green" in bands:
            gndvi_arr = self.gndvi(bands["nir"], bands["green"])
            out = output_dir / "gndvi.png"
            cv2.imwrite(str(out), self.colorize_index(gndvi_arr, -1, 1))
            results["gndvi"] = {
                "path": str(out),
                "mean": float(gndvi_arr.mean()),
                "array": gndvi_arr,
            }

        if "nir" in bands and "red" in bands:
            savi_arr = self.savi(bands["nir"], bands["red"])
            out = output_dir / "savi.png"
            cv2.imwrite(str(out), self.colorize_index(savi_arr, -1, 1))
            results["savi"] = {
                "path": str(out),
                "mean": float(savi_arr.mean()),
                "array": savi_arr,
            }

        return results
