# Domain Model

## CURRENT (Implemented)
- **Job**: Exists (`jobs` table).
- **Ranking**: Exists (`job_rankings` table).
- **Document**: Exists (`documents` table - CV, Cover Letter).
- **Application**: Exists (`applications` table).
- **ApplicationEvent**: Exists (`application_events` table).
- **Candidate Data**: Implemented in relational tables (via `002_candidate_kb.sql`), replacing the conceptual `cv-master.json` model.

## TARGET (Implemented in Database)

### 1. The Fact vs Presentation Boundary
The database strictly stores **FACTS** (stable attributes of the candidate like work history, specific bullets, earned certifications).
**PRESENTATION** (which facts to emphasize, summary paragraphs, rephrased bullets tailored to a job) is generated dynamically and temporarily during the Personalization phase. It is not stored as a core candidate fact.

### 2. Candidate Core Entities
- **candidate_profiles**: Personal info (name, email, phone, location, links).
- **candidate_experiences**: Company, role, start/end dates, location, modality.
- **candidate_experience_bullets**: Discrete text elements representing responsibilities or achievements linked to an experience. Stored individually to allow granular deterministic selection during CV generation.
- **candidate_projects**: Name, description, URL.
- **candidate_education**: Institution, degree, dates.
- **candidate_certifications**: Name, issuer, year.

### 3. Skill & Evidence Model
- **candidate_skills**: The canonical skill (e.g., "Python", "FastAPI"). Does not store "years of experience" manually; this is a derived metric calculated from linked experiences.
- **candidate_evidence**: A join table linking a skill to a source. 
  - **Decision Record (Exclusive Arc vs Polymorphic)**: Rather than using a weak polymorphic `source_id` UUID, the model implements an "Exclusive Arc". It features a strict `evidence_type` enum (`EXPERIENCE`, `PROJECT`, `CERTIFICATION`, `MANUAL`) paired with nullable foreign keys (`experience_id`, `project_id`, `certification_id`). A `CHECK` constraint ensures exactly one key is populated based on the type. This provides robust database-level referential integrity without excessive complexity.

### 4. Job Requirement Model (Future)
- **JobRequirement**: Extracted from raw job text.
  - `type`: skill, experience_duration, education, language.
  - `semantic_concept`: normalized term (e.g., "PostgreSQL").
  - `importance`: required vs preferred.

### 5. Matching Model (Future)
- **MatchResult**: The output of comparing a `JobRequirement` to the Candidate KB.
  - `status`: STRONG (has experience/project evidence), WEAK (manual claim only), or GAP (no evidence).
  - `evidence_refs`: Pointers to the specific `candidate_evidence` records that fulfill the requirement.
