"""
LinkedIn Connector
Portal: https://www.linkedin.com/jobs
Mercado: Global (incluye Chile)

Nota: LinkedIn tiene las restricciones anti-bot más estrictas.
Usar con rate limiting y sesiones guardadas. Respetar ToS.
"""

import os
import asyncio
from loguru import logger

from connectors.base import BaseConnector
from core.browser_client import BrowserClient
from core.llm_client import complete_json

PORTAL_NAME = "linkedin"
BASE_URL = "https://www.linkedin.com"
EMAIL = os.getenv("LINKEDIN_EMAIL", "")
PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")


class LinkedInConnector(BaseConnector):
    """
    Conector para LinkedIn Jobs.

    IMPORTANTE: LinkedIn tiene detección de bots avanzada.
    - Usar siempre sesión guardada (login manual previo)
    - Esperas aleatorias entre acciones
    - Limitar velocidad de búsqueda
    - Preferir Easy Apply para postulaciones
    """

    def __init__(self, browser: BrowserClient = None):
        super().__init__(browser or BrowserClient())

    async def search_jobs(
        self,
        keywords: list[str],
        location: str = "Chile",
        modality: str = "",
        max_results: int = 25,  # LinkedIn: max conservador
    ) -> list[dict]:
        jobs = []
        keyword_str = " ".join(keywords)

        # LinkedIn search URL
        location_param = location or "Chile"
        search_url = (
            f"{BASE_URL}/jobs/search?"
            f"keywords={keyword_str.replace(' ', '%20')}"
            f"&location={location_param.replace(' ', '%20')}"
        )

        if modality == "remote":
            search_url += "&f_WT=2"  # LinkedIn filter for remote

        logger.info(f"[linkedin] Buscando: {keyword_str} en {location_param}")

        try:
            # Cargar sesión guardada (necesita login previo)
            await self.browser.load_state(PORTAL_NAME)
            await self.browser.open_url(search_url)
            await asyncio.sleep(4)  # LinkedIn requiere esperas más largas

            page = 1
            while len(jobs) < max_results:
                snapshot = await self.browser.snapshot()
                page_jobs = await self._extract_jobs_llm(snapshot, PORTAL_NAME)

                if not page_jobs:
                    logger.info(f"[linkedin] Sin resultados en página {page}")
                    break

                jobs.extend(page_jobs)
                logger.info(f"[linkedin] Página {page}: {len(page_jobs)} ofertas")

                # LinkedIn: ir al siguiente grupo de resultados (scroll)
                has_next = await self._scroll_for_more()
                if not has_next:
                    break

                page += 1
                await asyncio.sleep(3)  # Rate limiting conservativo

        except Exception as e:
            logger.error(f"[linkedin] Error: {e}")

        return jobs[:max_results]

    def _normalize(self, raw: dict) -> dict:
        url = raw.get("url", "")
        if url and not url.startswith("http"):
            url = BASE_URL + url
        return {
            "external_id": url.split("/")[-1].split("?")[0] if url else "",
            "title": raw.get("title", "").strip(),
            "company": raw.get("company", "").strip(),
            "location": raw.get("location", "Chile").strip(),
            "modality": raw.get("modality") or self._detect_modality(raw.get("location", "")),
            "salary_min": None,
            "salary_max": None,
            "url": url,
            "description": raw.get("description", ""),
            "requirements": "",
            "posted_at": None,
            "raw_json": raw,
        }

    async def _scroll_for_more(self) -> bool:
        """Scroll down para cargar más resultados en LinkedIn."""
        try:
            await self.browser.scroll("down", 500)
            await asyncio.sleep(2)
            snapshot = await self.browser.snapshot()
            snap_text = str(snapshot).lower()
            # Verificar si hay botón "Ver más empleos" o paginación
            if "ver más" in snap_text or "show more" in snap_text or "siguiente" in snap_text:
                return True
            return False
        except Exception:
            return False

    async def navigate_to_apply(self, snapshot: dict) -> None:
        """Hace click en 'Solicitar empleo' o 'Easy Apply'."""
        try:
            snap_text = str(snapshot).lower()
            if "solicitud sencilla" in snap_text or "easy apply" in snap_text:
                await self.browser.find_and_click("Solicitud sencilla")
            else:
                await self.browser.find_and_click("Solicitar empleo")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"[linkedin] Error navigate_to_apply: {e}")
            raise

    async def fill_application_form(
        self,
        snapshot: dict,
        cv_path: str,
        cover_letter_path: str,
        personal_data: dict,
    ) -> None:
        """Completa el formulario de Easy Apply."""
        try:
            # Subir CV
            if cv_path:
                await self.browser.upload("#resume-upload", cv_path)
                await asyncio.sleep(1)

            # Completar campos básicos si están presentes
            snap_text = str(snapshot).lower()
            if "teléfono" in snap_text or "phone" in snap_text:
                await self.browser.find_and_fill("Teléfono", personal_data.get("phone", ""))

            logger.info("[linkedin] Formulario completado")
        except Exception as e:
            logger.error(f"[linkedin] Error fill_form: {e}")
            raise

    async def submit_application(self) -> None:
        """Envía la solicitud de Easy Apply."""
        try:
            # Puede haber múltiples pasos "Siguiente" antes del "Enviar solicitud"
            for _ in range(5):
                snapshot = await self.browser.snapshot()
                snap_text = str(snapshot).lower()
                if "enviar solicitud" in snap_text or "submit application" in snap_text:
                    await self.browser.find_and_click("Enviar solicitud")
                    await asyncio.sleep(2)
                    return
                elif "siguiente" in snap_text or "next" in snap_text:
                    await self.browser.find_and_click("Siguiente")
                    await asyncio.sleep(1)
                else:
                    break
        except Exception as e:
            logger.error(f"[linkedin] Error submit: {e}")
            raise

    async def login(self, email: str = None, password: str = None) -> bool:
        """
        Login manual en LinkedIn.
        Preferir hacer esto manualmente la primera vez y guardar la sesión.
        """
        email = email or EMAIL
        password = password or PASSWORD
        if not email or not password:
            logger.warning("[linkedin] Credenciales no configuradas")
            return False
        try:
            await self.browser.open_url(f"{BASE_URL}/login")
            await asyncio.sleep(3)
            await self.browser.find_and_fill("Correo electrónico", email)
            await self.browser.find_and_fill("Contraseña", password)
            await self.browser.find_and_click("Iniciar sesión")
            await asyncio.sleep(5)
            await self.browser.save_state(PORTAL_NAME)
            logger.info("[linkedin] Login exitoso")
            return True
        except Exception as e:
            logger.error(f"[linkedin] Login error: {e}")
            return False


def get_connector(browser: BrowserClient = None) -> LinkedInConnector:
    return LinkedInConnector(browser)
