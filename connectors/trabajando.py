"""
Trabajando.com Connector
Portal: https://www.trabajando.cl
Mercado: Chile
"""

import os
import asyncio
from loguru import logger

from connectors.base import BaseConnector
from core.browser_client import BrowserClient
from core.llm_client import complete_json

PORTAL_NAME = "trabajando"
BASE_URL = "https://www.trabajando.cl"
EMAIL = os.getenv("TRABAJANDO_EMAIL", "")
PASSWORD = os.getenv("TRABAJANDO_PASSWORD", "")


class TrabajandoConnector(BaseConnector):
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
        search_url = f"{BASE_URL}/trabajo/{keyword_str.replace(' ', '-').lower()}"

        logger.info(f"[trabajando] Buscando: {keyword_str}")

        try:
            await self.browser.open_url(search_url)
            await asyncio.sleep(3)

            page = 1
            while len(jobs) < max_results:
                snapshot = await self.browser.snapshot()
                page_jobs = await self._extract_jobs_llm(snapshot, PORTAL_NAME)

                if not page_jobs:
                    break

                jobs.extend(page_jobs)
                logger.info(f"[trabajando] Página {page}: {len(page_jobs)} ofertas")

                has_next = await self._next_page()
                if not has_next:
                    break
                page += 1
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"[trabajando] Error: {e}")

        return jobs[:max_results]

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
            await self.browser.open_url(f"{BASE_URL}/login")
            await asyncio.sleep(2)
            await self.browser.find_and_fill("email", email)
            await self.browser.find_and_fill("password", password)
            await self.browser.find_and_click("Ingresar")
            await asyncio.sleep(3)
            await self.browser.save_state(PORTAL_NAME)
            return True
        except Exception as e:
            logger.error(f"[trabajando] Login error: {e}")
            return False


def get_connector(browser: BrowserClient = None) -> TrabajandoConnector:
    return TrabajandoConnector(browser)
