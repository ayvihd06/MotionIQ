from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.config import STORAGE_DIR, CORS_ORIGINS
from app.api.routers import health, videos, analyses, auth, evolution, milestones, goals, focus, recommendations, weekly
from app.db.session import init_db

app = FastAPI(
    title="MotionIQ AI API",
    description="Explainable Computer Vision & AI Running Biomechanics Observation Platform",
    version="1.0.0"
)

# Configure CORS with Vercel regex support and configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database schema on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Mount local storage directory for video serving
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(videos.router)
app.include_router(analyses.router)
app.include_router(evolution.router)
app.include_router(milestones.router)
app.include_router(goals.router)
app.include_router(focus.router)
app.include_router(recommendations.router)
app.include_router(weekly.router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected backend error occurred.",
            "error_type": type(exc).__name__,
            "message": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
