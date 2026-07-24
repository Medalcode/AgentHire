"""
AgentHire — Discovery Agent
Busca ofertas de trabajo en todos los portales configurados.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv

from core.models import AgentRequest, AgentResponse, PortalName
from core.db import get_pool
from discovery.service import DiscoveryService

load_dotenv()

router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

discovery_service = DiscoveryService()


logger.info("Discovery Agent started")


@router.post("/run", response_model=AgentResponse)
async def run(request: AgentRequest):
    """
    Ejecuta una búsqueda de empleos.

    context esperado:
    {
        "portals": ["linkedin", "chiletrabajos"],  # opcional, default: todos
        "keywords": ["Python", "Backend"],
        "location": "Santiago",
        "modality": "remote",  # opcional
        "max_results_per_portal": 50
    }
    """
    if request.task not in ("discover_jobs", "discover"):
        raise HTTPException(status_code=400, detail=f"Task desconocida: {request.task}")

    try:
        result = await discovery_service.discover(request.context)
        return AgentResponse(
            status="success",
            result=result,
            artifacts=[],
        )
    except Exception as e:
        logger.exception(f"Error en discovery: {e}")
        return AgentResponse(
            status="error",
            result={},
            error=str(e),
        )


@router.get("/health")
async def health():
    return {"status": "ok", "agent": "discovery"}
