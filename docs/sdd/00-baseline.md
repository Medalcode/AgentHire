# Baseline: AgentHire Current State

## ACTUAL (Implemented)
- **FastAPI Monolith (`agent-backend`)**: Houses routers for discovery, ranking, apply, tracker, and optionally cv/cover generators.
- **n8n Orchestration**: Runs scheduled workflows (`01_discovery_cron.json`, `02_application_pipeline.json`) which call the FastAPI endpoints.
- **Database (PostgreSQL)**: Contains tables `jobs`, `job_rankings`, `documents`, `applications`, `application_events`, `portal_sessions`.
- **CV Generation**: Relies on a single `templates/cv-master.json` file as the source of truth, feeds it to an LLM, and produces a customized JSON which is then rendered via HTML to PDF (WeasyPrint).
- **Ranking**: Also uses `templates/cv-master.json` fed into an LLM to compare against job descriptions and output a match score/recommendation.
- **Dashboard (Next.js)**: Frontend interface.
- **Local LLMs**: Integration with Ollama for inference (`complete_json` in `core.llm_client`).

## PARTIAL / UNKNOWN
- **Browser/Apply Agent**: `portal_sessions` and Docker mentions `agent-browser` (Playwright), but actual application automation relies on implementation specifics not fully detailed in this audit.
- **Tracker**: Table `application_events` exists, but depth of tracking is unverified.

## OBSOLETE / RISKS
- Using a raw `cv-master.json` directly fed to LLMs encourages hallucination and lacks evidence traceability.
- Relying solely on LLMs to rewrite the CV without a structured gap/evidence model violates the "No Fabrication Principle".
