"""
AgentHire — Cover Letter Agent
Genera cartas de presentación personalizadas para cada oferta.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv

from core.models import AgentRequest, AgentResponse
from core.db import get_pool
from cover_letter.service import CoverLetterService

load_dotenv()

app = FastAPI(
    title="AgentHire — Cover Letter Agent",
    description="Genera cartas de presentación personalizadas",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

cover_service = CoverLetterService()


@app.on_event("startup")
async def startup():
    await get_pool()
    logger.info("Cover Letter Agent started")


@app.post("/run", response_model=AgentResponse)
async def run(request: AgentRequest):
    """
    Genera carta de presentación para una oferta.

    context:
    {
        "job_id": "uuid",
        "tone": "profesional"  # profesional | cercano | técnico
    }
    """
    if request.task not in ("generate_cover_letter", "cover_letter"):
        raise HTTPException(status_code=400, detail=f"Task desconocida: {request.task}")

    job_id = request.context.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id requerido")

    try:
        result = await cover_service.generate(job_id, request.context)
        return AgentResponse(
            status="success",
            result=result,
            artifacts=[result.get("pdf_path", "")],
        )
    except Exception as e:
        logger.exception(f"Error generando carta: {e}")
        return AgentResponse(status="error", result={}, error=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "cover-letter"}
