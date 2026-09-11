# Security and Privacy

## CURRENT STATE
- **IMPLEMENTED**: Uses local LLMs (Ollama) which ensures PII (Personally Identifiable Information) in CVs is not sent to third-party APIs.
- **IMPLEMENTED**: Credentials managed via `.env`.

## TARGET DIRECTION
- Maintain local LLMs as the default for privacy.
- Ensure the database securing the Candidate Knowledge Base has appropriate access controls.
- Playwright sessions (`portal_sessions`) must be stored securely and rotated.
