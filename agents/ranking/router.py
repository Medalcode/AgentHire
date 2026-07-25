"""
AgentHire — Ranking Agent
Analiza la compatibilidad entre un candidato y una oferta de trabajo usando IA.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv

from core.models import AgentRequest, AgentResponse
from core.db import get_pool
from ranking.service import RankingService

load_dotenv()

router = APIRouter()


ranking_service = RankingService()


logger.info("Ranking Agent started")


@router.post("/run", response_model=AgentResponse)
async def run(request: AgentRequest):
    """
    Analiza la compatibilidad de un job con el perfil del candidato.

    context esperado:
    {
        "job_id": "uuid",
        "score_threshold": 70  # opcional, default 70
    }
    """
    if request.task not in ("rank_job", "rank"):
        raise HTTPException(status_code=400, detail=f"Task desconocida: {request.task}")

    job_id = request.context.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id requerido")

    try:
        result = await ranking_service.rank(job_id, request.context)
        return AgentResponse(status="success", result=result)
    except Exception as e:
        logger.exception(f"Error en ranking: {e}")
        return AgentResponse(status="error", result={}, error=str(e))


@router.post("/run/batch", response_model=AgentResponse)
async def run_batch(request: AgentRequest):
    """
    Rankea múltiples jobs en paralelo.

    context esperado:
    {
        "job_ids": ["uuid1", "uuid2", ...],
        "score_threshold": 70
    }
    """
    job_ids = request.context.get("job_ids", [])
    if not job_ids:
        raise HTTPException(status_code=400, detail="job_ids requerido")

    try:
        result = await ranking_service.rank_batch(job_ids, request.context)
        return AgentResponse(status="success", result=result)
    except Exception as e:
        logger.exception(f"Error en ranking batch: {e}")
        return AgentResponse(status="error", result={}, error=str(e))


@router.get("/health")
async def health():
    return {"status": "ok", "agent": "ranking"}
