"""
Ranking Service — analiza compatibilidad candidato-oferta con LLM.
"""

import asyncio
import json
from pathlib import Path
from loguru import logger

from core.db import fetch_one, fetch_all, execute
from core.llm_client import complete_json


# Carga el CV maestro una vez al iniciar
CV_MASTER_PATH = Path(__file__).parent.parent.parent / "templates" / "cv-master.json"

def _load_cv_master() -> dict:
    if CV_MASTER_PATH.exists():
        return json.loads(CV_MASTER_PATH.read_text(encoding="utf-8"))
    logger.warning("cv-master.json no encontrado, usando CV vacío")
    return {}


CV_MASTER = _load_cv_master()

# Carga el prompt de ranking
RANKING_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "ranking.md"

def _load_ranking_prompt() -> str:
    if RANKING_PROMPT_PATH.exists():
        return RANKING_PROMPT_PATH.read_text(encoding="utf-8")
    return "Analiza la compatibilidad del candidato con la oferta de trabajo. Responde en JSON."


SYSTEM_PROMPT = _load_ranking_prompt()


class RankingService:
    async def rank(self, job_id: str, context: dict) -> dict:
        """Analiza un solo job."""
        job = await fetch_one("SELECT * FROM jobs WHERE id = $1", job_id)
        if not job:
            raise ValueError(f"Job no encontrado: {job_id}")

        ranking = await self._analyze_job(job, context)

        # Guardar en BD
        await self._save_ranking(job_id, ranking)

        return ranking

    async def rank_batch(self, job_ids: list[str], context: dict) -> dict:
        """Analiza múltiples jobs en paralelo (máx 5 a la vez)."""
        semaphore = asyncio.Semaphore(5)

        async def rank_with_semaphore(job_id: str):
            async with semaphore:
                try:
                    return await self.rank(job_id, context)
                except Exception as e:
                    logger.error(f"Error rankeando {job_id}: {e}")
                    return {"job_id": job_id, "error": str(e)}

        results = await asyncio.gather(
            *[rank_with_semaphore(jid) for jid in job_ids],
            return_exceptions=False,
        )

        applied = [r for r in results if r.get("recommendation") == "apply"]
        skipped = [r for r in results if r.get("recommendation") == "skip"]
        manual = [r for r in results if r.get("recommendation") == "manual_review"]

        return {
            "total": len(results),
            "apply": len(applied),
            "skip": len(skipped),
            "manual_review": len(manual),
            "results": results,
        }

    async def _analyze_job(self, job: dict, context: dict) -> dict:
        """Llama al LLM para analizar compatibilidad."""
        score_threshold = context.get("score_threshold", 70)

        # Construir el prompt con el job y el CV
        user_prompt = f"""
## Oferta de Trabajo

**Empresa**: {job['company']}
**Cargo**: {job['title']}
**Portal**: {job['portal']}
**Ubicación**: {job.get('location', 'No especificada')}
**Modalidad**: {job.get('modality', 'No especificada')}

**Descripción**:
{job.get('description', 'Sin descripción')}

**Requisitos**:
{job.get('requirements', 'Sin requisitos especificados')}

---

## Perfil del Candidato

{json.dumps(CV_MASTER, ensure_ascii=False, indent=2)}

---

Umbral mínimo de score para recomendar aplicar: {score_threshold}

Analiza la compatibilidad y responde ÚNICAMENTE con el JSON especificado en el system prompt.
"""

        try:
            result = await complete_json(
                prompt=user_prompt,
                system=SYSTEM_PROMPT,
            )
            result["job_id"] = str(job["id"])
            result["job_title"] = job["title"]
            result["company"] = job["company"]
            return result
        except Exception as e:
            logger.error(f"Error LLM para job {job['id']}: {e}")
            # Fallback conservativo
            return {
                "job_id": str(job["id"]),
                "job_title": job["title"],
                "company": job["company"],
                "score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "recommendation": "manual_review",
                "cv_template": "general",
                "reasoning": f"Error al analizar: {str(e)}",
                "red_flags": [],
            }

    async def _save_ranking(self, job_id: str, ranking: dict) -> None:
        """Guarda el ranking en la BD y actualiza el status del job."""
        sql = """
            INSERT INTO job_rankings (job_id, score, skills_match, recommendation, cv_template, analysis)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT DO NOTHING
        """
        skills_match = json.dumps({
            "matched": ranking.get("matched_skills", []),
            "missing": ranking.get("missing_skills", []),
        })

        await execute(
            sql,
            job_id,
            ranking.get("score", 0),
            skills_match,
            ranking.get("recommendation", "manual_review"),
            ranking.get("cv_template", "general"),
            ranking.get("reasoning", ""),
        )

        # Actualizar status del job a 'ranked'
        await execute(
            "UPDATE jobs SET status = 'ranked' WHERE id = $1",
            job_id,
        )
