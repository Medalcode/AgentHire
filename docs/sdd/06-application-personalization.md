# Application Personalization

## CURRENT STATE
- **IMPLEMENTED**: `cv_generator/service.py` feeds `cv-master.json` and the job description to the LLM and says "Personalize this".
- **RISKS**: The LLM can fabricate experience, alter metrics, or generate completely fictional bullet points (violating the No Fabrication Principle).

## TARGET DIRECTION

### The CV Generation Pipeline
Personalization is the act of turning **Facts** into **Presentation** without altering the truth.

1. **Deterministic Selection (Code, not LLM)**:
   - The system looks at the `MatchResult`s for the job.
   - It selects the `CandidateExperienceBullet`s that mention the strongly matched skills.
   - It drops irrelevant bullets to keep the CV concise.
   - It reorders the `CandidateSkill` categories to put matched skills at the top.

2. **LLM Refinement (Constrained LLM Boundary)**:
   - The LLM is provided ONLY with the *selected* facts (the filtered bullets, the matched skills, the job details).
   - Prompt: "Write a 3-sentence professional summary based STRICTLY on these selected facts. Do not invent metrics. You may slightly rephrase the provided bullets to match the job's vocabulary (e.g. 'microservices' instead of 'distributed systems'), but you may not alter the meaning or numbers."

3. **Validation**:
   - The system can optionally verify that the LLM didn't introduce hallucinated skills into the summary by doing a strict keyword check against the Candidate KB.

4. **Human Review**:
   - The final document is presented on the dashboard. The user approves it, and any manual edits they make could be parsed back as new evidence if they add new skills.
