# Implementation Roadmap

1. **Phase 1 — Candidate Knowledge Foundation**: Migrate `cv-master.json` to relational Candidate Knowledge Base tables.
2. **Phase 2 — Job Intelligence**: Update discovery/ranking to extract discrete `JobRequirement`s instead of doing a full-pass match.
3. **Phase 3 — Evidence-Based Matching**: Implement the logic to map `JobRequirement`s to `Evidence` in the KB.
4. **Phase 4 — Personalized Documents**: Update `cv_generator` to build CVs deterministically from the matching evidence, using LLMs only for text refinement.
5. **Phase 5 — Human Review**: Enhance dashboard capabilities to allow editing and approving generated documents.
6. **Phase 6 — Browser/Application Assistance**: Refine the `apply` agent to assist humans rather than autonomously submit.
7. **Phase 7 — LinkedIn Integration**: Stabilize job source ingestion.
8. **Phase 8 — Advanced Optimization**: Feedback loops from human edits back to the Knowledge Base.
