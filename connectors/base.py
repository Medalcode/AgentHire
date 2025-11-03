"""
Base Connector — clase base para todos los conectores de portales.
Define la interfaz que deben implementar.
"""

from abc import ABC, abstractmethod
from typing import Optional
from loguru import logger


class BaseConnector(ABC):
    """
    Interfaz común para todos los conectores de portales de empleo.
    Cada conector encapsula los selectores y flujos específicos del portal.
    """

    def __init__(self, browser=None):
        self.browser = browser

    @abstractmethod
    async def search_jobs(
        self,
        keywords: list[str],
        location: str = "",
        modality: str = "",
        max_results: int = 50,
    ) -> list[dict]:
        """
        Busca ofertas en el portal.

        Retorna lista de dicts con:
        {
            "external_id": str,
            "title": str,
            "company": str,
            "location": str,
            "modality": str,
            "salary_min": int | None,
            "salary_max": int | None,
            "url": str,
            "description": str,
            "requirements": str,
            "posted_at": datetime | None,
            "raw_json": dict,
        }
        """
        ...

    async def navigate_to_apply(self, snapshot: dict) -> None:
        """Navega al formulario de aplicación desde el detalle del job."""
        raise NotImplementedError(f"{self.__class__.__name__} no soporta apply")

    async def fill_application_form(
        self,
        snapshot: dict,
        cv_path: str,
        cover_letter_path: str,
        personal_data: dict,
    ) -> None:
        """Completa el formulario de postulación."""
        raise NotImplementedError(f"{self.__class__.__name__} no soporta fill_form")

    async def answer_additional_questions(self, snapshot: dict) -> None:
        """Responde preguntas adicionales del formulario con IA."""
        pass  # Opcional — no todos los portales tienen preguntas adicionales

    async def submit_application(self) -> None:
        """Envía la postulación."""
        raise NotImplementedError(f"{self.__class__.__name__} no soporta submit")

    async def update_profile(self, profile_data: dict) -> bool:
        """Actualiza el perfil del candidato en el portal."""
        raise NotImplementedError(f"{self.__class__.__name__} no soporta update_profile")

    async def login(self, email: str, password: str) -> bool:
        """Inicia sesión en el portal."""
        raise NotImplementedError(f"{self.__class__.__name__} no soporta login")

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _parse_salary(self, salary_text: str) -> tuple[Optional[int], Optional[int]]:
        """Parsea texto de salario y retorna (min, max) en CLP."""
        import re
        if not salary_text:
            return None, None

        # Remover puntos de miles y convertir comas
        cleaned = re.sub(r"[.\s]", "", salary_text.replace(",", "."))
        numbers = re.findall(r"\d+\.?\d*", cleaned)

        if len(numbers) >= 2:
            return int(float(numbers[0])), int(float(numbers[1]))
        elif len(numbers) == 1:
            val = int(float(numbers[0]))
            return val, val
        return None, None

    def _detect_modality(self, text: str) -> str:
        """Detecta modalidad del trabajo desde texto."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["remoto", "remote", "teletrabajo", "trabajo desde casa"]):
            return "remote"
        if any(w in text_lower for w in ["híbrido", "hybrid", "mixto"]):
            return "hybrid"
        if any(w in text_lower for w in ["presencial", "oficina", "in-office"]):
            return "presencial"
        return "unknown"
