"""
AgentHire — CV Generator Agent
Genera CVs personalizados en PDF para cada oferta de trabajo.
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
from cv_generator.service import CVGeneratorService

load_dotenv()

app = FastAPI(
    title="AgentHire — CV Generator Agent",
    description="Genera CVs personalizados en PDF para cada oferta",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

cv_service = CVGeneratorService()


@app.on_event("startup")
async def startup():
    await get_pool()
    logger.info("CV Generator Agent started")


@app.post("/run", response_model=AgentResponse)
async def run(request: AgentRequest):
    """
    Genera un CV personalizado para una oferta específica.

    context esperado:
    {
        "job_id": "uuid",
        "template": "backend"  # opcional, se toma del ranking si no se especifica
    }
    """
    if request.task not in ("generate_cv", "cv"):
        raise HTTPException(status_code=400, detail=f"Task desconocida: {request.task}")

    job_id = request.context.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id requerido")

    try:
        result = await cv_service.generate(job_id, request.context)
        return AgentResponse(
            status="success",
            result=result,
            artifacts=[result.get("pdf_path", "")],
        )
    except Exception as e:
        logger.exception(f"Error generando CV: {e}")
        return AgentResponse(status="error", result={}, error=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "cv-generator"}
