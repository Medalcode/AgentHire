# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **CI/CD**: GitHub Actions pipeline for backend (Pytest) and frontend (Next.js build).
- **Security**: `.dockerignore` to prevent `.env` and `__pycache__` leakage into production containers.
- **QA Strategy**: Pure function unit tests (`test_parsers.py`), integration tests (`test_db_integration.py`), and smoke tests (`test_api_smoke.py`).

### Changed
- **Architecture**: Migrated 7 independent Python agent microservices into a single "Majestic Monolith" backend (`agents/main.py`).
- **Infrastructure**: Reduced Docker Compose services from 7 backend containers to 1 (`agent-backend:8000`), saving ~1GB RAM locally.
- **Routing**: Agents now act as `APIRouter` modules within the monolithic backend (`/discovery`, `/apply`, `/tracker`, etc.).
- **Dashboard API**: Updated frontend proxy URLs to point to the new monolithic backend.

### Fixed
- **Core LLM Client**: Replaced `try/except Exception` with specific error handling and robust fallback parsers for Markdown JSON fences and JSON arrays.
- **Dashboard**: Fixed React SVG nesting hydration errors, unhandled `alert` loops, and localized relative time formatting (CLP/es-CL).
- **Connectors**: Enhanced error resilience in the `_parse_salary` base connector implementation.

### Removed
- **Brittle Tests**: Deleted `test_db.py` and `test_llm_client.py` which utilized deep mocking and provided 0% business logic coverage.
- **Code Duplication**: Removed 7 redundant `main.py` entrypoints and 7 redundant `Dockerfile`s across agent subdirectories.
