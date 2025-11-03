"""
Apply Service — aplica a empleos usando agent-browser vía MCP.
"""

import os
import asyncio
import importlib
from datetime import datetime
from pathlib import Path
from loguru import logger

from core.db import fetch_one, execute
from core.browser_client import BrowserClient

REQUIRE_HUMAN_APPROVAL = os.getenv("REQUIRE_HUMAN_APPROVAL", "true").lower() == "true"

PORTAL_CONNECTORS = {
    "linkedin": "connectors.linkedin",
    "chiletrabajos": "connectors.chiletrabajos",
    "computrabajo": "connectors.computrabajo",
    "trabajando": "connectors.trabajando",
    "laborum": "connectors.laborum",
}


class ApplyService:
    def __init__(self):
        self.browser = BrowserClient()

    async def apply(self, application_id: str, context: dict) -> dict:
        """Ejecuta el flujo completo de postulación para una application."""

        # Obtener application con todo el contexto necesario
        application = await fetch_one(
            """
            SELECT a.*, j.portal, j.url as job_url, j.title, j.company,
                   cv.path as cv_path, cl.path as cover_letter_path
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            LEFT JOIN documents cv ON a.cv_doc_id = cv.id
            LEFT JOIN documents cl ON a.cover_doc_id = cl.id
            WHERE a.id = $1
            """,
            application_id,
        )

        if not application:
            raise ValueError(f"Application no encontrada: {application_id}")

        portal = application["portal"]
        logger.info(f"Aplicando a: {application['company']} - {application['title']} via {portal}")

        require_approval = context.get("require_human_approval", REQUIRE_HUMAN_APPROVAL)

        screenshots = []

        try:
            # Cargar sesión del portal
            await self.browser.load_state(portal)
            logger.info(f"Sesión de {portal} cargada")

            # Navegar a la oferta
            await self.browser.open_url(application["job_url"])
            await asyncio.sleep(2)  # Esperar carga

            # Tomar snapshot para entender la página
            snapshot = await self.browser.snapshot()

            # Llamar al conector específico del portal
            connector_module = importlib.import_module(PORTAL_CONNECTORS[portal])
            connector = connector_module.get_connector(self.browser)

            # Paso 1: Preparar la aplicación (click en Apply button)
            await connector.navigate_to_apply(snapshot)
            await asyncio.sleep(1)

            # Screenshot de confirmación antes de aplicar
            screenshot_before = await self.browser.screenshot(
                f"/app/outputs/screenshots/{application_id}_before.png"
            )
            screenshots.append(screenshot_before)

            # Human in the loop — espera aprobación antes de continuar
            if require_approval:
                logger.info(
                    f"⚠️  HUMAN APPROVAL REQUIRED para {application['company']}. "
                    f"Screenshot guardado en: {screenshot_before}. "
                    "Esperando señal de aprobación (POST /approve/{application_id})..."
                )
                await self._wait_for_approval(application_id, timeout_seconds=3600)

            # Paso 2: Completar formulario
            snapshot_form = await self.browser.snapshot()
            await connector.fill_application_form(
                snapshot=snapshot_form,
                cv_path=application["cv_path"],
                cover_letter_path=application["cover_letter_path"],
                personal_data=await self._get_personal_data(),
            )

            # Paso 3: Responder preguntas adicionales con LLM si las hay
            await connector.answer_additional_questions(snapshot_form)

            # Paso 4: Submit
            await connector.submit_application()

            # Screenshot de confirmación
            await asyncio.sleep(2)
            screenshot_after = await self.browser.screenshot(
                f"/app/outputs/screenshots/{application_id}_after.png"
            )
            screenshots.append(screenshot_after)

            # Actualizar BD
            await execute(
                """
                UPDATE applications SET
                    status = 'applied',
                    applied_at = NOW(),
                    human_approved = $2,
                    confirmation_screenshot = $3
                WHERE id = $1
                """,
                application_id,
                require_approval,
                screenshot_after,
            )

            await execute("UPDATE jobs SET status = 'applied' WHERE id = $1", application["job_id"])

            # Registrar evento
            await execute(
                "INSERT INTO application_events (application_id, event_type) VALUES ($1, 'applied')",
                application_id,
            )

            logger.info(f"✅ Aplicación enviada exitosamente a {application['company']}")

            return {
                "success": True,
                "application_id": application_id,
                "company": application["company"],
                "title": application["title"],
                "screenshots": screenshots,
                "applied_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error aplicando a {application.get('company', 'N/A')}: {e}")
            await execute(
                "UPDATE applications SET status = 'discarded', notes = $2 WHERE id = $1",
                application_id,
                f"Error: {str(e)}",
            )
            raise

    async def _get_personal_data(self) -> dict:
        """Retorna datos personales del candidato (del cv-master.json)."""
        import json
        cv_path = Path(__file__).parent.parent.parent / "templates" / "cv-master.json"
        if cv_path.exists():
            cv = json.loads(cv_path.read_text())
            return cv.get("personal", {})
        return {}

    async def _wait_for_approval(self, application_id: str, timeout_seconds: int = 3600):
        """
        Espera a que la aplicación sea aprobada manualmente.
        La aprobación se señala actualizando human_approved=true en la BD.
        """
        start = asyncio.get_event_loop().time()
        while True:
            row = await fetch_one(
                "SELECT human_approved FROM applications WHERE id = $1", application_id
            )
            if row and row["human_approved"]:
                logger.info(f"Aprobación recibida para {application_id}")
                return

            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > timeout_seconds:
                raise TimeoutError(f"Timeout esperando aprobación manual para {application_id}")

            await asyncio.sleep(10)  # Chequear cada 10 segundos
