"""
AgentHire — Tracker Agent
Gestiona el historial de postulaciones y expone una API REST para el dashboard.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv
from typing import Optional
from datetime import date

from core.models import AgentRequest, AgentResponse
from core.db import get_pool, fetch_all, fetch_one, execute

load_dotenv()

app = FastAPI(
    title="AgentHire — Tracker Agent",
    description="Gestiona historial de postulaciones y provee API para el dashboard",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    await get_pool()
    logger.info("Tracker Agent started")


# ─── Dashboard API ────────────────────────────────────────────────────────────

@app.get("/stats")
async def get_stats():
    """Estadísticas generales para el dashboard."""
    total_jobs = await fetch_one("SELECT COUNT(*) as count FROM jobs")
    total_applied = await fetch_one(
        "SELECT COUNT(*) as count FROM applications WHERE status != 'discarded'"
    )
    total_interviews = await fetch_one(
        "SELECT COUNT(*) as count FROM application_events WHERE event_type = 'interview_scheduled'"
    )
    total_offers = await fetch_one(
        "SELECT COUNT(*) as count FROM application_events WHERE event_type = 'offer_received'"
    )

    # Jobs por portal
    by_portal = await fetch_all(
        "SELECT portal, COUNT(*) as count FROM jobs GROUP BY portal ORDER BY count DESC"
    )

    # Jobs por status
    by_status = await fetch_all(
        "SELECT status, COUNT(*) as count FROM jobs GROUP BY status ORDER BY count DESC"
    )

    # Score promedio de los rankeados
    avg_score = await fetch_one(
        "SELECT AVG(score) as avg FROM job_rankings WHERE recommendation = 'apply'"
    )

    applied_count = total_applied["count"] if total_applied else 0
    interviews_count = total_interviews["count"] if total_interviews else 0
    success_rate = round((interviews_count / applied_count * 100) if applied_count > 0 else 0, 1)

    return {
        "total_jobs_found": total_jobs["count"] if total_jobs else 0,
        "total_applied": applied_count,
        "total_interviews": interviews_count,
        "total_offers": total_offers["count"] if total_offers else 0,
        "success_rate": success_rate,
        "avg_match_score": round(float(avg_score["avg"] or 0), 1) if avg_score else 0,
        "by_portal": [dict(r) for r in by_portal],
        "by_status": [dict(r) for r in by_status],
    }


@app.get("/jobs")
async def get_jobs(
    portal: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lista jobs con filtros y paginación."""
    conditions = ["1=1"]
    params = []
    i = 1

    if portal:
        conditions.append(f"j.portal = ${i}")
        params.append(portal)
        i += 1
    if status:
        conditions.append(f"j.status = ${i}")
        params.append(status)
        i += 1
    if min_score is not None:
        conditions.append(f"r.score >= ${i}")
        params.append(min_score)
        i += 1
    if search:
        conditions.append(f"(j.title ILIKE ${i} OR j.company ILIKE ${i})")
        params.append(f"%{search}%")
        i += 1

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    sql = f"""
        SELECT j.id, j.portal, j.title, j.company, j.location, j.modality,
               j.url, j.status, j.discovered_at,
               r.score, r.recommendation, r.cv_template
        FROM jobs j
        LEFT JOIN job_rankings r ON r.job_id = j.id
        WHERE {where}
        ORDER BY j.discovered_at DESC
        LIMIT {page_size} OFFSET {offset}
    """

    count_sql = f"""
        SELECT COUNT(*) as total FROM jobs j
        LEFT JOIN job_rankings r ON r.job_id = j.id
        WHERE {where}
    """

    jobs = await fetch_all(sql, *params)
    total = await fetch_one(count_sql, *params)

    return {
        "items": [dict(j) for j in jobs],
        "total": total["total"] if total else 0,
        "page": page,
        "page_size": page_size,
    }


@app.get("/applications")
async def get_applications(
    status: Optional[str] = Query(None),
    portal: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lista postulaciones con filtros."""
    conditions = ["1=1"]
    params = []
    i = 1

    if status:
        conditions.append(f"a.status = ${i}")
        params.append(status)
        i += 1
    if portal:
        conditions.append(f"j.portal = ${i}")
        params.append(portal)
        i += 1

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    sql = f"""
        SELECT a.id, a.status, a.applied_at, a.human_approved, a.notes,
               j.title, j.company, j.portal, j.url as job_url,
               cv.filename as cv_filename, cv.path as cv_path,
               cl.filename as cover_letter_filename
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        LEFT JOIN documents cv ON a.cv_doc_id = cv.id
        LEFT JOIN documents cl ON a.cover_doc_id = cl.id
        WHERE {where}
        ORDER BY a.applied_at DESC
        LIMIT {page_size} OFFSET {offset}
    """

    apps = await fetch_all(sql, *params)
    total = await fetch_one(
        f"SELECT COUNT(*) as total FROM applications a JOIN jobs j ON a.job_id = j.id WHERE {where}",
        *params,
    )

    return {
        "items": [dict(a) for a in apps],
        "total": total["total"] if total else 0,
        "page": page,
        "page_size": page_size,
    }


@app.patch("/applications/{application_id}/status")
async def update_application_status(application_id: str, body: dict):
    """Actualiza el status de una postulación (para actualizaciones manuales)."""
    new_status = body.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status requerido")

    await execute(
        "UPDATE applications SET status = $2 WHERE id = $1",
        application_id,
        new_status,
    )

    event_map = {
        "interview": "interview_scheduled",
        "offer": "offer_received",
        "rejected": "rejected",
        "withdrawn": "withdrawn",
    }

    if new_status in event_map:
        await execute(
            "INSERT INTO application_events (application_id, event_type) VALUES ($1, $2)",
            application_id,
            event_map[new_status],
        )

    return {"success": True}


@app.patch("/applications/{application_id}/approve")
async def approve_application(application_id: str):
    """Aprueba manualmente una postulación (signal para el apply-agent)."""
    await execute(
        "UPDATE applications SET human_approved = true WHERE id = $1",
        application_id,
    )
    return {"success": True, "message": f"Application {application_id} aprobada"}


@app.get("/documents")
async def get_documents(
    doc_type: Optional[str] = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lista documentos generados."""
    conditions = ["1=1"]
    params = []
    i = 1

    if doc_type:
        conditions.append(f"d.type = ${i}")
        params.append(doc_type)
        i += 1

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    sql = f"""
        SELECT d.id, d.type, d.filename, d.path, d.template_used, d.generated_at,
               j.title as job_title, j.company
        FROM documents d
        LEFT JOIN jobs j ON d.job_id = j.id
        WHERE {where}
        ORDER BY d.generated_at DESC
        LIMIT {page_size} OFFSET {offset}
    """

    docs = await fetch_all(sql, *params)
    total = await fetch_one(
        f"SELECT COUNT(*) as total FROM documents d WHERE {where}", *params
    )

    return {
        "items": [dict(d) for d in docs],
        "total": total["total"] if total else 0,
        "page": page,
        "page_size": page_size,
    }


@app.get("/report/daily")
async def daily_report():
    """Reporte diario para n8n."""
    from datetime import datetime, timedelta

    yesterday = datetime.utcnow() - timedelta(days=1)

    new_jobs = await fetch_one(
        "SELECT COUNT(*) as count FROM jobs WHERE discovered_at >= $1", yesterday
    )
    new_applications = await fetch_one(
        "SELECT COUNT(*) as count FROM applications WHERE applied_at >= $1", yesterday
    )
    new_events = await fetch_all(
        """
        SELECT ae.event_type, j.company, j.title
        FROM application_events ae
        JOIN applications a ON ae.application_id = a.id
        JOIN jobs j ON a.job_id = j.id
        WHERE ae.occurred_at >= $1
        ORDER BY ae.occurred_at DESC
        """,
        yesterday,
    )

    return {
        "date": datetime.utcnow().date().isoformat(),
        "new_jobs_discovered": new_jobs["count"] if new_jobs else 0,
        "new_applications_sent": new_applications["count"] if new_applications else 0,
        "events": [dict(e) for e in new_events],
        "generated_at": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "tracker"}
