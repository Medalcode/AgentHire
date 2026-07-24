import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from core.db import get_pool, close_pool

# Import routers from agents
from discovery.router import router as discovery_router
from ranking.router import router as ranking_router
from apply.router import router as apply_router
from tracker.router import router as tracker_router

# Some modules might not be fully implemented yet, import them conditionally or comment them out
try:
    from cv_generator.router import router as cv_router
    has_cv = True
except ImportError:
    has_cv = False

try:
    from cover_letter.router import router as cover_router
    has_cover = True
except ImportError:
    has_cover = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await get_pool()
    yield
    # Shutdown
    await close_pool()

app = FastAPI(
    title="AgentHire Backend",
    description="Majestic Monolith for all AgentHire AI Agents",
    version="1.0.0",
    lifespan=lifespan
)

# Mount all the Agent routers
app.include_router(discovery_router, prefix="/discovery", tags=["Discovery"])
app.include_router(ranking_router, prefix="/ranking", tags=["Ranking"])
app.include_router(apply_router, prefix="/apply", tags=["Apply"])
app.include_router(tracker_router, prefix="/tracker", tags=["Tracker"])

if has_cv:
    app.include_router(cv_router, prefix="/cv", tags=["CV Generator"])
if has_cover:
    app.include_router(cover_router, prefix="/cover", tags=["Cover Letter"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "agent-backend"}
