from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import upload, stitching, analysis

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="드론 RGB/멀티스펙트럴 이미지 정합 및 밭작물 면적·생육 진단 API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(stitching.router)
app.include_router(analysis.router)

# 정적 파일 서빙 (결과 이미지)
app.mount("/outputs", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="outputs")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
