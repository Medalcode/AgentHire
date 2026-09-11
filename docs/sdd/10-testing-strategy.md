# Testing Strategy

## CURRENT STATE
- **IMPLEMENTED**: Mention of QA strategy, Smoke/Integration tests in `README.md`.

## TARGET DIRECTION
- SDD (Specification-Driven Development) mandates strict adherence to the documented models.
- **Testing Focus**: Test the extraction of requirements and the evidence-matching logic rigorously, ensuring the "No Fabrication Principle" is mathematically enforced in the code, rather than just prompted in the LLM.
- **Mocking**: Minimize fragile mocks, use actual local LLM inference in integration tests where feasible, or use deterministic stub responses for speed.
