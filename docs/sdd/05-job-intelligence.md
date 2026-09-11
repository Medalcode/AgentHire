# Job Intelligence Specification

## 1. Current Implementation
- **IMPLEMENTED**: Job discovery extracts basic metadata (title, company, modality, `experience_years_min`).
- **PARTIAL**: The `job-extractor.md` prompt extracts a monolithic `requirements` string (raw text block).
- **MISSING**: There is no intermediate step that breaks the `requirements` text block into discrete, structured, and auditable requirement entities. Ranking happens implicitly via a massive LLM prompt.

## 2. Proposed JobRequirement Model
The Job Intelligence layer introduces a formal contract between unstructured job descriptions and the deterministic matching engine.

```text
Entity: JobRequirement
- id: UUID
- job_id: UUID (FK to jobs)
- req_type: Enum (SKILL, EXPERIENCE, EDUCATION, LANGUAGE, CERTIFICATION)
- semantic_concept: String (Normalized representation)
- raw_text: String (Original wording from the job description)
- is_required: Boolean (True = Required, False = Preferred)
- extractor_version: Integer (Tracking schema/prompt versions)
```

## 3. Requirement Types
- **SKILL**: Specific tools, frameworks, paradigms (e.g., Python, React, TDD).
- **EXPERIENCE**: Time-based constraints (e.g., "3+ years in backend"). Can optionally hold a `constraint_value` (e.g., 3).
- **EDUCATION**: Degree requirements (e.g., "Bachelor's in Computer Science").
- **LANGUAGE**: Language proficiency (e.g., "Advanced English").
- **CERTIFICATION**: Formal certifications (e.g., "AWS Certified").

## 4. Required vs Preferred
The extraction LLM must explicitly classify a requirement as `REQUIRED` (is_required: true) or `PREFERRED` (is_required: false) based on the textual context (e.g., "Must have" vs "Nice to have"). The matching engine uses this distinction to calculate strict eligibility.

## 5. Normalization Strategy
**Decision:** Option B (Canonical table + LLM Semantic Matching) is the MVP choice.
- **Why**: Maintaining a rigid manual alias dictionary is brittle. A heavy embedding/VectorDB search is overkill for MVP and harms explainability. 
- **How**: The LLM will be instructed to extract the `semantic_concept` in its standard canonical form (e.g., converting "ReactJS" in raw text to "React" as the concept). The matching engine then attempts exact matches against `CandidateSkill.name`. If false negatives occur frequently, we can introduce a lightweight alias list or soft-matching later.

## 6. Experience Constraints
Experience requirements are complex. "3 years of Python" should NOT be modeled as just a SKILL requirement for "Python".
It should be modeled as an EXPERIENCE requirement:
- `semantic_concept`: "Python"
- `constraint_value`: 3 (years)
- `raw_text`: "3+ años de experiencia con Python"
The matching engine will later compute candidate experience duration from `candidate_experiences` linked to the "Python" skill.

## 7. Provenance & Versioning
Every requirement must preserve its `raw_text` to prove why it exists. The `extractor_version` field tracks which prompt/pipeline generated the requirement. If the prompt improves, we can safely delete old requirements for a job and re-run extraction without losing the original job description.

## 8. LLM Boundary & Failure Handling
- **Permitted**: Identifying requirements, classifying required vs preferred, extracting raw phrases, proposing semantic concepts.
- **Prohibited**: The LLM must not decide if the candidate meets the requirement.
- **Failure**: If the LLM returns invalid JSON, missing fields, or obvious hallucinations (e.g., requirements not present in the text), the extraction fails entirely for that job. The job status remains 'discovered' (unprocessed) until manually reviewed or retried. Duplicate semantic concepts within the same job should be deduplicated by keeping the stricter constraint (e.g., REQUIRED overrides PREFERRED).

## 9. Matching Contract
The Job Intelligence output is an array of `JobRequirement` objects.
The Matching Engine consumes this array, iterates over it, and queries the Candidate Knowledge Base for Evidence. The Matching Engine never reads the raw job description.
