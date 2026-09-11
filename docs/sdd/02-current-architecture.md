# Current Architecture

## Components

### ACTUAL
- **agent-backend**: FastAPI monolith exposing endpoints (`/discovery`, `/ranking`, `/cv`, `/cover`, `/apply`, `/tracker`).
- **n8n**: Orchestrates the cron jobs and workflows, calling the FastAPI endpoints.
- **agent-browser**: A separate container (likely Playwright-based) for interacting with job portals.
- **Database**: PostgreSQL with schema defined in `001_init.sql` (jobs, rankings, applications, docs).
- **dashboard**: Next.js UI.
- **Local LLMs**: Ollama (qwen2.5-coder:7b).

## Data Flow (Actual)
1. **Discovery**: Scrapes jobs -> saves to `jobs` table.
2. **Ranking**: Reads job + `cv-master.json` -> calls LLM -> saves to `job_rankings`.
3. **CV Gen**: Reads job + `cv-master.json` -> calls LLM -> renders HTML -> PDF (WeasyPrint) -> saves to `documents`.

## INTENDED (Target Architecture Evolution)
- Evolve from `cv-master.json` to a structured `Candidate Knowledge Base` in the database.
- Keep the Majestic Monolith (FastAPI) as it simplifies deployment and orchestration.
- Make the CV generation pipeline deterministic by querying the knowledge base rather than throwing the whole JSON to the LLM to rewrite.
