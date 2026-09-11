# Job Analysis and Matching

*(See `docs/sdd/05-job-intelligence.md` for the detailed Job Intelligence and Requirement Extraction specification).*

## CURRENT STATE
- **IMPLEMENTED**: `ranking/service.py` receives a job and `cv-master.json`, prompting the LLM to output a match score and `skills_match` array in one pass.
- **RISKS**: The LLM relies on holistic interpretation. It can hallucinate matches or miss implicit ones because it isn't forced to evaluate requirements discretely.

## TARGET DIRECTION

### 1. Job Requirement Extraction (LLM Boundary)
An Extractor Agent reads the raw job description and extracts an array of `JobRequirement` objects.
- Example: "Python", "Required", "Experience"
- The LLM's job stops here. It turns unstructured text into structured requirements.

### 2. Evidence-Based Matching (Deterministic Boundary)
The system iterates through each `JobRequirement`.
- It searches the Candidate KB for a matching `CandidateSkill`.
- If found, it retrieves all `CandidateEvidence` for that skill.
- The `MatchResult` is constructed deterministically:
  - If Evidence = Experience/Project -> **STRONG MATCH**.
  - If Evidence = Manual Claim -> **WEAK MATCH**.
  - If no Evidence -> **GAP**.

### 3. Scoring
The overall job score is a mathematical function of the `MatchResult`s (e.g., % of 'Required' skills that have 'STRONG' matches), NOT an arbitrary number invented by the LLM.

This model enables explainability:
"We matched you 85% because you have Evidence for Python (from AgentHire project) and FastAPI (from Empresa Ejemplo SA), but you lack evidence for AWS."
