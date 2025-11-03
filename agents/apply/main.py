"""
AgentHire — Apply Agent
Aplica automáticamente a ofertas de trabajo usando agent-browser MCP.
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
from apply.service import ApplyService

load_dotenv()

app = FastAPI(
    title="AgentHire — Apply Agent",
    description="Aplica a ofertas de trabajo usando automatización del navegador",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

apply_service = ApplyService()


@app.on_event("startup")
async def startup():
    await get_pool()
    logger.info("Apply Agent started")


@app.post("/run", response_model=AgentResponse)
async def run(request: AgentRequest):
    """
    Aplica a una oferta de trabajo.

    context esperado:
    {
        "application_id": "uuid",  # Registro de application ya creado
        "require_human_approval": true  # Override del env var
    }
    """
    if request.task not in ("apply_job", "apply"):
        raise HTTPException(status_code=400, detail=f"Task desconocida: {request.task}")

    application_id = request.context.get("application_id")
    if not application_id:
        raise HTTPException(status_code=400, detail="application_id requerido")

    try:
        result = await apply_service.apply(application_id, request.context)
        return AgentResponse(
            status="success",
            result=result,
            artifacts=result.get("screenshots", []),
        )
    except Exception as e:
        logger.exception(f"Error en apply: {e}")
        return AgentResponse(status="error", result={}, error=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "apply"}
