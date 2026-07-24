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

        # Remove thousands separators (dots) and whitespace
        cleaned = salary_text.replace(".", "").replace(" ", "")
        # Replace comma decimal separator with dot for float parsing
        cleaned = cleaned.replace(",", ".")
        numbers = re.findall(r"\d+", cleaned)

        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            return int(numbers[0]), int(numbers[0])
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

    async def _extract_jobs_llm(self, snapshot: dict, portal_name: str) -> list[dict]:
        """
        Extrae datos de ofertas desde el accessibility tree usando LLM.
        """
        from core.llm_client import complete_json
        
        snap_text = str(snapshot)[:8000]
        prompt = f"""
Extrae las ofertas de trabajo del accessibility tree de {portal_name}.
Retorna JSON array: [{{"title":"","company":"","location":"","url":"","salary_text":""}}]
Solo con datos reales del árbol. Si no hay datos, retorna [].

Accessibility tree:
{snap_text}
"""
        try:
            result = await complete_json(prompt=prompt, system="Extrae datos de ofertas de trabajo en JSON.")
            if isinstance(result, list):
                return [self._normalize(j) for j in result if j.get("title") or j.get("url")]
            return []
        except Exception as e:
            logger.warning(f"[{portal_name}] LLM error en _extract_jobs_llm: {e}")
            return []
            
    def _normalize(self, raw: dict) -> dict:
        """Normaliza un job al formato estándar. Debe ser sobreescrito."""
        raise NotImplementedError
