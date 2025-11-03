"""
Cover Letter Service — genera cartas de presentación con LLM + WeasyPrint.
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from loguru import logger

from core.db import fetch_one, execute
from core.llm_client import complete

CV_MASTER_PATH = Path(__file__).parent.parent.parent / "templates" / "cv-master.json"
PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "cover-letter.md"
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/outputs"))


def _load_cv() -> dict:
    if CV_MASTER_PATH.exists():
        return json.loads(CV_MASTER_PATH.read_text(encoding="utf-8"))
    return {}


def _load_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "Escribe una carta de presentación profesional en español para el candidato y la oferta."


CV_MASTER = _load_cv()
SYSTEM_PROMPT = _load_prompt()


class CoverLetterService:
    async def generate(self, job_id: str, context: dict) -> dict:
        job = await fetch_one("SELECT * FROM jobs WHERE id = $1", job_id)
        if not job:
            raise ValueError(f"Job no encontrado: {job_id}")

        tone = context.get("tone", "profesional")
        personal = CV_MASTER.get("personal", {})
        summary = CV_MASTER.get("summary", "")

        logger.info(f"Generando carta para: {job['company']} - {job['title']} (tono: {tone})")

        # Generar texto con LLM
        letter_md = await self._generate_letter(job, personal, summary, tone)

        # Renderizar a PDF
        pdf_path = await self._render_pdf(letter_md, job, personal)

        # Guardar en BD
        doc_id = await self._save_document(job_id, pdf_path, tone)

        return {
            "document_id": str(doc_id),
            "pdf_path": str(pdf_path),
            "tone": tone,
            "job_title": job["title"],
            "company": job["company"],
        }

    async def _generate_letter(
        self, job: dict, personal: dict, summary: str, tone: str
    ) -> str:
        prompt = f"""
## Datos de la oferta:
- Empresa: {job['company']}
- Cargo: {job['title']}
- Descripción: {job.get('description', 'No disponible')}
- Requisitos: {job.get('requirements', 'No disponibles')}

## Datos del candidato:
- Nombre: {personal.get('name', '')}
- Email: {personal.get('email', '')}
- Resumen: {summary}
- LinkedIn: {personal.get('linkedin', '')}

## Tono solicitado: {tone}

Escribe la carta de presentación completa en español.
"""
        letter_text = await complete(prompt=prompt, system=SYSTEM_PROMPT)
        return letter_text

    async def _render_pdf(self, letter_md: str, job: dict, personal: dict) -> Path:
        from weasyprint import HTML
        import markdown as md

        # Convertir Markdown a HTML
        letter_html = md.markdown(letter_md)

        date_str = datetime.now().strftime("%d de %B de %Y")

        full_html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap');
        body {{
            font-family: 'Inter', sans-serif;
            font-size: 11pt;
            line-height: 1.7;
            color: #1a1a2e;
            padding: 25mm 20mm;
            max-width: 700px;
            margin: 0 auto;
        }}
        .header {{
            margin-bottom: 30px;
        }}
        .header h2 {{
            font-size: 16pt;
            color: #1a1a2e;
            margin-bottom: 5px;
        }}
        .header .contact {{
            color: #666;
            font-size: 10pt;
        }}
        .date {{ color: #666; margin-bottom: 20px; }}
        .body p {{ margin-bottom: 12px; text-align: justify; }}
        .signature {{ margin-top: 40px; }}
        .signature strong {{ display: block; color: #6366f1; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>{personal.get('name', '')}</h2>
        <div class="contact">
            {personal.get('email', '')} · {personal.get('phone', '')} · {personal.get('location', '')}
        </div>
    </div>
    <p class="date">{date_str}</p>
    <div class="body">
        {letter_html}
    </div>
</body>
</html>
"""
        hash_key = hashlib.md5(
            f"{job['id']}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:8]
        filename = f"carta_{job['company'].lower().replace(' ', '_')}_{hash_key}.pdf"

        output_path = OUTPUT_DIR / "cover_letters"
        output_path.mkdir(parents=True, exist_ok=True)
        pdf_path = output_path / filename

        HTML(string=full_html).write_pdf(str(pdf_path))
        logger.info(f"Carta generada: {pdf_path}")

        return pdf_path

    async def _save_document(self, job_id: str, pdf_path: Path, template: str) -> str:
        result = await execute(
            """
            INSERT INTO documents (job_id, type, filename, path, template_used)
            VALUES ($1, 'cover_letter', $2, $3, $4)
            RETURNING id
            """,
            job_id,
            pdf_path.name,
            str(pdf_path),
            template,
            fetch=True,
        )
        return result["id"] if result else None
