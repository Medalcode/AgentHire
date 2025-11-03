"""
Discovery Service — coordina la búsqueda en todos los portales.
"""

import asyncio
from datetime import datetime
from loguru import logger

from core.db import fetch_all, execute
from core.models import PortalName

# Importa cada conector dinámicamente
PORTAL_CONNECTORS = {
    "linkedin": "connectors.linkedin.LinkedInConnector",
    "chiletrabajos": "connectors.chiletrabajos.ChileTrabajosConnector",
    "computrabajo": "connectors.computrabajo.ComputrabajoConnector",
    "trabajando": "connectors.trabajando.TrabajandoConnector",
    "laborum": "connectors.laborum.LaborumConnector",
}

DEFAULT_PORTALS = list(PORTAL_CONNECTORS.keys())


class DiscoveryService:
    async def discover(self, context: dict) -> dict:
        portals = context.get("portals", DEFAULT_PORTALS)
        keywords = context.get("keywords", [])
        location = context.get("location", "")
        modality = context.get("modality", "")
        max_results = context.get("max_results_per_portal", 50)

        if not keywords:
            raise ValueError("Se requiere al menos un keyword para buscar")

        logger.info(f"Iniciando discovery en portales: {portals}")

        # Ejecutar búsquedas en paralelo
        tasks = []
        for portal_name in portals:
            connector = await self._get_connector(portal_name)
            if connector:
                tasks.append(
                    self._search_portal(
                        connector, portal_name, keywords, location, modality, max_results
                    )
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_found = 0
        total_new = 0
        all_job_ids = []

        for portal_name, result in zip(portals, results):
            if isinstance(result, Exception):
                logger.error(f"Error en portal {portal_name}: {result}")
                continue
            total_found += result["found"]
            total_new += result["new"]
            all_job_ids.extend(result["job_ids"])

        logger.info(f"Discovery completado: {total_found} encontradas, {total_new} nuevas")

        return {
            "jobs_found": total_found,
            "new_jobs": total_new,
            "job_ids": all_job_ids,
            "portals_searched": portals,
            "searched_at": datetime.utcnow().isoformat(),
        }

    async def _get_connector(self, portal_name: str):
        """Importa dinámicamente el conector del portal."""
        import importlib

        if portal_name not in PORTAL_CONNECTORS:
            logger.warning(f"Conector no encontrado para portal: {portal_name}")
            return None

        class_path = PORTAL_CONNECTORS[portal_name]
        module_path, class_name = class_path.rsplit(".", 1)
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            return cls()
        except ImportError as e:
            logger.error(f"No se pudo cargar conector {portal_name}: {e}")
            return None

    async def _search_portal(
        self, connector, portal_name: str, keywords, location, modality, max_results
    ) -> dict:
        """Busca en un portal y guarda los resultados en la BD."""
        try:
            jobs = await connector.search_jobs(
                keywords=keywords,
                location=location,
                modality=modality,
                max_results=max_results,
            )
            logger.info(f"  [{portal_name}] Encontradas {len(jobs)} ofertas")

            new_jobs = []
            for job in jobs:
                inserted = await self._save_job(portal_name, job)
                if inserted:
                    new_jobs.append(inserted)

            return {
                "found": len(jobs),
                "new": len(new_jobs),
                "job_ids": [str(j["id"]) for j in new_jobs],
            }
        except Exception as e:
            logger.error(f"Error buscando en {portal_name}: {e}")
            raise

    async def _save_job(self, portal_name: str, job: dict) -> dict | None:
        """
        Guarda un job en la BD.
        Retorna el job insertado o None si ya existía (deduplicación por URL).
        """
        sql = """
            INSERT INTO jobs (portal, external_id, title, company, location, modality,
                              salary_min, salary_max, url, description, requirements, posted_at, raw_json)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (url) DO NOTHING
            RETURNING *
        """
        try:
            result = await execute(
                sql,
                portal_name,
                job.get("external_id"),
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                job.get("modality", ""),
                job.get("salary_min"),
                job.get("salary_max"),
                job.get("url", ""),
                job.get("description", ""),
                job.get("requirements", ""),
                job.get("posted_at"),
                str(job.get("raw_json", {})),
                fetch=True,
            )
            return result
        except Exception as e:
            logger.error(f"Error guardando job {job.get('url')}: {e}")
            return None
