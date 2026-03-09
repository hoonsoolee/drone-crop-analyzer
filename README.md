# 드론 작물 분석기 (Drone Crop Analyzer)

드론으로 촬영한 RGB 및 멀티스펙트럴 이미지를 빠르게 정합하고,
밭작물의 **재배 면적 산출** 및 **생육 상태 진단**을 제공하는 웹 기반 소프트웨어입니다.

## 주요 기능

| 기능 | 설명 |
|------|------|
| 🔗 이미지 정합 | OpenCV 기반 RGB/멀티스펙트럴 드론 이미지 모자이크·정합 |
| 🌾 작물 감지 | HSV 색상 + ExG 식생 지수 기반 작물 마스크 생성 |
| 📐 면적 산출 | GSD(Ground Sampling Distance) 기반 실제 면적(m², ha, 평) 산출 |
| 📊 생육 진단 | NDVI, NDRE, GNDVI, SAVI 지수 분석 → 우수/양호/주의/불량 등급화 |
| 🗺️ 시각화 | 작물 마스크·NDVI 컬러맵 오버레이 표시 |

## 지원 작물

배추 · 양파 · 마늘 · 고추 · 감자 · 무 · 상추 · 시금치 · 고구마

## 지원 이미지 타입

- **RGB**: JPG, PNG, TIFF (DJI, Parrot 등 일반 카메라)
- **멀티스펙트럴**: Red / Green / Blue / NIR / RedEdge 밴드별 TIFF (MicaSense RedEdge, Parrot Sequoia 등)

## 빠른 시작

### 1. Docker Compose (권장)

```bash
git clone https://github.com/<your-username>/drone-crop-analyzer.git
cd drone-crop-analyzer
docker-compose up --build
```

브라우저에서 `http://localhost` 접속

### 2. 로컬 개발

**백엔드**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**프론트엔드**
```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속
API 문서: `http://localhost:8000/docs`

## 사용 방법

1. **이미지 업로드** 탭 → RGB 또는 멀티스펙트럴 선택 → 이미지 파일 드래그 업로드
2. **업로드 및 정합 시작** 클릭 → 자동 모자이크 처리
3. **작물 분석** 탭 → 작물 종류 선택 → 분석 시작
4. 면적(m², ha), 피복률, NDVI, 생육 등급, 권고사항 확인

## 기술 스택

- **Backend**: Python 3.11 · FastAPI · OpenCV · NumPy
- **Frontend**: React 18 · Vite · Tailwind CSS · Leaflet.js · Recharts
- **인프라**: Docker · Docker Compose · Nginx

## GSD (Ground Sampling Distance) 설정

기본값은 100m 고도 DJI Phantom 4 Pro 기준 `2.74 cm/pixel`입니다.
카메라/고도에 따라 `backend/app/services/area_calculator.py`의 `DEFAULT_GSD_CM` 값을 조정하세요.

| 드론 | 고도 | GSD |
|------|------|-----|
| DJI Phantom 4 Pro | 100m | 2.74 cm/px |
| DJI Mini 3 Pro | 100m | 3.7 cm/px |
| MicaSense RedEdge | 120m | 8.0 cm/px |

## 라이선스

MIT License
