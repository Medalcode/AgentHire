# Candidate Knowledge Base

## CURRENT STATE
- **IMPLEMENTED**: The knowledge base schema exists in PostgreSQL via `002_candidate_kb.sql`.
- **LEGACY**: The system still utilizes `templates/cv-master.json` temporarily while application logic is refactored.

## TARGET DIRECTION
The Candidate KB is the repository of **Candidate Facts**. 

### Migration Strategy (Mapping `cv-master.json` to SQL)
The current JSON will eventually map to the new schema as follows:

- `personal` → **candidate_profiles** (1:1 mapping).
- `summary` → **DO NOT MIGRATE AS FACT**. A summary is presentation logic. It will be generated per job dynamically.
- `experience` → **candidate_experiences** (1:1 mapping mapping periods to start_date/end_date).
- `experience.bullets` → **candidate_experience_bullets**. Each string becomes a distinct row to allow deterministic selection per job.
- `experience.technologies` → Creates a **candidate_skills** record (if missing) and a **candidate_evidence** row linking the `skill_id` to the `experience_id` (Type: EXPERIENCE).
- `skills` → **candidate_skills**. If a skill exists here but not in any experience/project, it gets a **candidate_evidence** row (Type: MANUAL).
- `projects` → **candidate_projects** (1:1 mapping).
- `projects.technologies` → Creates **candidate_evidence** row linking `skill_id` to `project_id` (Type: PROJECT).
- `education`, `certifications` → 1:1 mappings to respective tables.

### Fact Boundaries
The LLM will NEVER be allowed to INSERT facts into the Candidate Knowledge Base autonomously. Facts are extracted from the user's input/CV initially, but the system of record becomes rigid. Any new facts must be verified by the human.
