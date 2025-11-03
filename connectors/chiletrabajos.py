"""
ChileTrabajos Connector
Portal: https://www.chiletrabajos.cl
Mercado: Chile

Estrategia de scraping:
- Búsqueda via URL parameters
- Paginación con scroll infinito o botón "Ver más"
- Extracción de datos del accessibility tree (agent-browser snapshot)
"""

import os
import asyncio
from datetime import datetime
from loguru import logger

from connectors.base import BaseConnector
from core.browser_client import BrowserClient
from core.llm_client import complete_json


PORTAL_NAME = "chiletrabajos"
BASE_URL = "https://www.chiletrabajos.cl"
EMAIL = os.getenv("CHILETRABAJOS_EMAIL", "")
PASSWORD = os.getenv("CHILETRABAJOS_PASSWORD", "")


class ChileTrabajosConnector(BaseConnector):
    """
    Conector para ChileTrabajos.cl

    ChileTrabajos permite búsqueda sin login. El login es opcional
    para postulación directa. Usamos agent-browser para navegar.
    """

    def __init__(self, browser: BrowserClient = None):
        super().__init__(browser or BrowserClient())

    async def search_jobs(
        self,
        keywords: list[str],
        location: str = "",
        modality: str = "",
        max_results: int = 50,
    ) -> list[dict]:
        """Busca ofertas en ChileTrabajos."""
        jobs = []
        keyword_str = " ".join(keywords)

        search_url = f"{BASE_URL}/empleos?q={keyword_str.replace(' ', '+')}"
        if location:
            search_url += f"&ciudad={location.replace(' ', '+')}"

        logger.info(f"[chiletrabajos] Buscando: {keyword_str} | URL: {search_url}")

        try:
            await self.browser.open_url(search_url)
            await asyncio.sleep(3)

            page_num = 1
            while len(jobs) < max_results:
                snapshot = await self.browser.snapshot()
                page_jobs = await self._extract_jobs_llm(snapshot, PORTAL_NAME)

                if not page_jobs:
                    logger.info(f"[chiletrabajos] No más resultados en página {page_num}")
                    break

                jobs.extend(page_jobs)
                logger.info(
                    f"[chiletrabajos] Página {page_num}: {len(page_jobs)} ofertas extraídas"
                )

                # Intentar ir a la siguiente página
                has_next = await self._go_to_next_page()
                if not has_next:
                    break

                page_num += 1
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"[chiletrabajos] Error en búsqueda: {e}")

        logger.info(f"[chiletrabajos] Total: {len(jobs)} ofertas")
        return jobs[:max_results]

    def _normalize(self, raw: dict) -> dict:
        """Normaliza un job al formato estándar."""
        salary_min, salary_max = self._parse_salary(raw.get("salary_text", ""))
        return {
            "external_id": raw.get("url", "").split("/")[-1],
            "title": raw.get("title", "").strip(),
            "company": raw.get("company", "").strip(),
            "location": raw.get("location", "Chile").strip(),
            "modality": self._detect_modality(raw.get("title", "") + " " + raw.get("location", "")),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "url": raw.get("url", ""),
            "description": raw.get("description", ""),
            "requirements": raw.get("requirements", ""),
            "posted_at": None,
            "raw_json": raw,
        }

    async def _go_to_next_page(self) -> bool:
        """Intenta ir a la siguiente página. Retorna False si no hay más."""
        try:
            snapshot = await self.browser.snapshot()
            snap_text = str(snapshot).lower()
            if "siguiente" in snap_text or "next" in snap_text:
                await self.browser.find_and_click("siguiente")
                await asyncio.sleep(2)
                return True
            return False
        except Exception:
            return False

    async def login(self, email: str = None, password: str = None) -> bool:
        """Inicia sesión en ChileTrabajos."""
        email = email or EMAIL
        password = password or PASSWORD

        if not email or not password:
            logger.warning("[chiletrabajos] Credenciales no configuradas")
            return False

        try:
            await self.browser.open_url(f"{BASE_URL}/login")
            await asyncio.sleep(2)
            await self.browser.find_and_fill("email", email)
            await self.browser.find_and_fill("password", password)
            await self.browser.find_and_click("Iniciar sesión")
            await asyncio.sleep(3)
            await self.browser.save_state(PORTAL_NAME)
            logger.info("[chiletrabajos] Login exitoso")
            return True
        except Exception as e:
            logger.error(f"[chiletrabajos] Error en login: {e}")
            return False


def get_connector(browser: BrowserClient = None) -> ChileTrabajosConnector:
    return ChileTrabajosConnector(browser)
