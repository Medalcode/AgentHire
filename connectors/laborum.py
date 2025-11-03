"""
Laborum Connector
Portal: https://www.laborum.cl
Mercado: Chile, Perú, Colombia
"""

import os
import asyncio
from loguru import logger

from connectors.base import BaseConnector
from core.browser_client import BrowserClient
from core.llm_client import complete_json

PORTAL_NAME = "laborum"
BASE_URL = "https://www.laborum.cl"
EMAIL = os.getenv("LABORUM_EMAIL", "")
PASSWORD = os.getenv("LABORUM_PASSWORD", "")


class LaborumConnector(BaseConnector):
    def __init__(self, browser: BrowserClient = None):
        super().__init__(browser or BrowserClient())

    async def search_jobs(
        self,
        keywords: list[str],
        location: str = "",
        modality: str = "",
        max_results: int = 50,
    ) -> list[dict]:
        jobs = []
        keyword_str = " ".join(keywords)
        # Laborum usa búsqueda via query params
        search_url = (
            f"{BASE_URL}/empleos?"
            f"q={keyword_str.replace(' ', '+')}"
            + (f"&region={location.replace(' ', '+')}" if location else "")
        )

        logger.info(f"[laborum] Buscando: {keyword_str}")

        try:
            await self.browser.open_url(search_url)
            await asyncio.sleep(3)

            page = 1
            while len(jobs) < max_results:
                snapshot = await self.browser.snapshot()
                page_jobs = await self._extract_jobs_llm(snapshot)

                if not page_jobs:
                    break

                jobs.extend(page_jobs)
                logger.info(f"[laborum] Página {page}: {len(page_jobs)} ofertas")

                has_next = await self._next_page()
                if not has_next:
                    break
                page += 1
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"[laborum] Error: {e}")

        return jobs[:max_results]

    async def _extract_jobs_llm(self, snapshot: dict) -> list[dict]:
        snap_text = str(snapshot)[:8000]
        prompt = f"""
Extrae las ofertas de trabajo del accessibility tree de Laborum.cl.
Retorna JSON array con: title, company, location, url, salary_text.
Si no hay datos, retorna [].

Tree:
{snap_text}
"""
        try:
            result = await complete_json(prompt=prompt, system="Extrae datos de trabajo en JSON.")
            if isinstance(result, list):
                return [self._normalize(j) for j in result if j.get("title")]
            return []
        except Exception as e:
            logger.warning(f"[laborum] LLM error: {e}")
            return []

    def _normalize(self, raw: dict) -> dict:
        salary_min, salary_max = self._parse_salary(raw.get("salary_text", ""))
        url = raw.get("url", "")
        if url and not url.startswith("http"):
            url = BASE_URL + url
        return {
            "external_id": url.split("/")[-1] if url else "",
            "title": raw.get("title", "").strip(),
            "company": raw.get("company", "").strip(),
            "location": raw.get("location", "Chile").strip(),
            "modality": self._detect_modality(raw.get("title", "")),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "url": url,
            "description": "",
            "requirements": "",
            "posted_at": None,
            "raw_json": raw,
        }

    async def _next_page(self) -> bool:
        try:
            snapshot = await self.browser.snapshot()
            if "siguiente" in str(snapshot).lower():
                await self.browser.find_and_click("Siguiente")
                await asyncio.sleep(2)
                return True
        except Exception:
            pass
        return False

    async def login(self, email: str = None, password: str = None) -> bool:
        email = email or EMAIL
        password = password or PASSWORD
        if not email or not password:
            return False
        try:
            await self.browser.open_url(f"{BASE_URL}/acceso")
            await asyncio.sleep(2)
            await self.browser.find_and_fill("email", email)
            await self.browser.find_and_fill("password", password)
            await self.browser.find_and_click("Ingresar")
            await asyncio.sleep(3)
            await self.browser.save_state(PORTAL_NAME)
            return True
        except Exception as e:
            logger.error(f"[laborum] Login error: {e}")
            return False


def get_connector(browser: BrowserClient = None) -> LaborumConnector:
    return LaborumConnector(browser)
