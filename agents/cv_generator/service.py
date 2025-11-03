"""
CV Generator Service — personaliza y genera PDFs de CV.
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from loguru import logger

from core.db import fetch_one, execute
from core.llm_client import complete_json
def _get_root_dir() -> Path:
    p = Path(__file__).resolve()
    return p.parent.parent if (p.parent.parent / "templates").exists() else p.parent.parent.parent

ROOT_DIR = _get_root_dir()


CV_MASTER_PATH = ROOT_DIR / "templates" / "cv-master.json"
PROMPTS_PATH = ROOT_DIR / "prompts" / "cv-generator.md"
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/outputs"))


def _load_cv_master() -> dict:
    if CV_MASTER_PATH.exists():
        return json.loads(CV_MASTER_PATH.read_text(encoding="utf-8"))
    return {}


def _load_prompt() -> str:
    if PROMPTS_PATH.exists():
        return PROMPTS_PATH.read_text(encoding="utf-8")
    return "Personaliza el CV para la oferta de trabajo. Responde en JSON con el CV adaptado."


CV_MASTER = _load_cv_master()
SYSTEM_PROMPT = _load_prompt()


class CVGeneratorService:
    async def generate(self, job_id: str, context: dict) -> dict:
        # Obtener datos del job
        job = await fetch_one("SELECT * FROM jobs WHERE id = $1", job_id)
        if not job:
            raise ValueError(f"Job no encontrado: {job_id}")

        # Obtener ranking para saber qué template usar
        ranking = await fetch_one(
            "SELECT * FROM job_rankings WHERE job_id = $1 ORDER BY ranked_at DESC LIMIT 1",
            job_id,
        )
        template = context.get("template") or (ranking["cv_template"] if ranking else "general")

        logger.info(f"Generando CV template={template} para: {job['company']} - {job['title']}")

        # Personalizar CV con LLM
        customized_cv = await self._customize_cv(job, template)

        # Generar PDF
        pdf_path = await self._render_pdf(customized_cv, job)

        # Guardar en BD
        doc_id = await self._save_document(job_id, pdf_path, template)

        return {
            "document_id": str(doc_id),
            "pdf_path": str(pdf_path),
            "template": template,
            "job_title": job["title"],
            "company": job["company"],
        }

    async def _customize_cv(self, job: dict, template: str) -> dict:
        """Usa LLM para personalizar el CV según el job."""
        user_prompt = f"""
## Oferta de trabajo a la que aplicar:

**Empresa**: {job['company']}
**Cargo**: {job['title']}
**Descripción**: {job.get('description', '')}
**Requisitos**: {job.get('requirements', '')}

## CV Maestro (base):
{json.dumps(CV_MASTER, ensure_ascii=False, indent=2)}

## Template solicitado: {template}

Personaliza el CV para esta oferta específica. Responde con el CV adaptado en formato JSON.
"""
        try:
            return await complete_json(prompt=user_prompt, system=SYSTEM_PROMPT)
        except Exception as e:
            logger.warning(f"Error personalizando con LLM, usando CV base: {e}")
            return CV_MASTER

    async def _render_pdf(self, cv_data: dict, job: dict) -> Path:
        """Renderiza el CV personalizado a PDF usando WeasyPrint."""
        from weasyprint import HTML

        html_content = self._cv_to_html(cv_data, job)

        # Crear nombre único para el archivo
        hash_key = hashlib.md5(
            f"{job['id']}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:8]
        filename = f"cv_{job['company'].lower().replace(' ', '_')}_{hash_key}.pdf"

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = OUTPUT_DIR / "cvs" / filename
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        HTML(string=html_content).write_pdf(str(pdf_path))
        logger.info(f"CV generado: {pdf_path}")

        return pdf_path

    def _cv_to_html(self, cv: dict, job: dict) -> str:
        """Convierte el CV a HTML con estilos profesionales."""
        personal = cv.get("personal", CV_MASTER.get("personal", {}))
        skills = cv.get("skills", CV_MASTER.get("skills", {}))
        experience = cv.get("experience", CV_MASTER.get("experience", []))
        education = cv.get("education", CV_MASTER.get("education", []))
        projects = cv.get("projects", CV_MASTER.get("projects", []))
        languages_spoken = cv.get("languages_spoken", CV_MASTER.get("languages_spoken", []))
        summary = cv.get("summary", CV_MASTER.get("summary", ""))

        # Experiencia HTML
        exp_html = ""
        for exp in experience:
            bullets_html = "".join(f"<li>{b}</li>" for b in exp.get("bullets", []))
            exp_html += f"""
            <div class="exp-item">
                <div class="exp-header">
                    <strong>{exp.get('role', '')}</strong>
                    <span class="period">{exp.get('period', '')}</span>
                </div>
                <div class="exp-company">{exp.get('company', '')} · {exp.get('location', '')} · {exp.get('modality', '')}</div>
                <ul>{bullets_html}</ul>
            </div>
            """

        # Skills HTML
        all_skills = []
        for category in skills.values():
            if isinstance(category, list):
                all_skills.extend(category)
        skills_html = "".join(f'<span class="skill-tag">{s}</span>' for s in all_skills)

        # Educación HTML
        edu_html = ""
        for edu in education:
            edu_html += f"""
            <div class="edu-item">
                <strong>{edu.get('degree', '')}</strong><br>
                {edu.get('institution', '')} · {edu.get('period', '')}
            </div>
            """

        # Proyectos HTML
        proj_html = ""
        for proj in projects:
            techs = ", ".join(proj.get("technologies", []))
            proj_html += f"""
            <div class="proj-item">
                <strong>{proj.get('name', '')}</strong> — {proj.get('description', '')}<br>
                <small>Tecnologías: {techs}</small>
            </div>
            """

        # Idiomas
        lang_html = " · ".join(
            f"{l.get('language', '')} ({l.get('level', '')})" for l in languages_spoken
        )

        return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            font-size: 10pt;
            color: #1a1a2e;
            line-height: 1.5;
            padding: 20mm 18mm;
        }}
        h1 {{ font-size: 22pt; color: #1a1a2e; letter-spacing: -0.5px; }}
        h2 {{
            font-size: 11pt;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #6366f1;
            border-bottom: 1.5px solid #6366f1;
            padding-bottom: 4px;
            margin: 16px 0 8px 0;
        }}
        .contact {{ color: #555; font-size: 9pt; margin-top: 4px; }}
        .contact a {{ color: #6366f1; text-decoration: none; }}
        .summary {{ color: #333; margin: 8px 0 4px 0; font-size: 9.5pt; }}
        .exp-item {{ margin-bottom: 12px; }}
        .exp-header {{ display: flex; justify-content: space-between; }}
        .exp-header strong {{ color: #1a1a2e; font-size: 10.5pt; }}
        .period {{ color: #6366f1; font-size: 9pt; }}
        .exp-company {{ color: #666; font-size: 9pt; margin: 2px 0 4px 0; }}
        ul {{ padding-left: 16px; }}
        li {{ margin-bottom: 3px; font-size: 9.5pt; color: #333; }}
        .skill-tag {{
            display: inline-block;
            background: #ede9fe;
            color: #4f46e5;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 8.5pt;
            margin: 2px;
            font-weight: 500;
        }}
        .edu-item {{ margin-bottom: 8px; font-size: 9.5pt; }}
        .proj-item {{ margin-bottom: 8px; font-size: 9.5pt; color: #333; }}
        .lang {{ font-size: 9.5pt; color: #333; }}
    </style>
</head>
<body>
    <h1>{personal.get('name', '')}</h1>
    <div class="contact">
        {personal.get('email', '')} · {personal.get('phone', '')} · {personal.get('location', '')}<br>
        <a href="https://{personal.get('linkedin', '')}">{personal.get('linkedin', '')}</a> ·
        <a href="https://{personal.get('github', '')}">{personal.get('github', '')}</a>
    </div>

    <h2>Perfil Profesional</h2>
    <p class="summary">{summary}</p>

    <h2>Experiencia</h2>
    {exp_html}

    <h2>Habilidades</h2>
    <div>{skills_html}</div>

    <h2>Educación</h2>
    {edu_html}

    {"<h2>Proyectos</h2>" + proj_html if projects else ""}

    <h2>Idiomas</h2>
    <p class="lang">{lang_html}</p>
</body>
</html>
"""

    async def _save_document(self, job_id: str, pdf_path: Path, template: str) -> str:
        result = await execute(
            """
            INSERT INTO documents (job_id, type, filename, path, template_used)
            VALUES ($1, 'cv', $2, $3, $4)
            RETURNING id
            """,
            job_id,
            pdf_path.name,
            str(pdf_path),
            template,
            fetch=True,
        )
        await execute("UPDATE jobs SET status = 'queued' WHERE id = $1", job_id)
        return result["id"] if result else None
