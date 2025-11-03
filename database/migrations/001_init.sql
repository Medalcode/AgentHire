-- =============================================================================
-- AgentHire — database/migrations/001_init.sql
-- Initial schema: job tracking, AI rankings, documents, applications, events.
--
-- Run via setup.sh:
--   docker compose exec postgres \
--     psql -U $POSTGRES_USER -d $POSTGRES_DB -f /migrations/001_init.sql
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extension: uuid-ossp — generates UUID v4 primary keys
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Enum: portal_name — supported job portals
-- ---------------------------------------------------------------------------
CREATE TYPE portal_name AS ENUM (
    'linkedin',
    'chiletrabajos',
    'computrabajo',
    'trabajando',
    'laborum'
);

-- ---------------------------------------------------------------------------
-- Enum: job_status — lifecycle of a discovered job
-- ---------------------------------------------------------------------------
CREATE TYPE job_status AS ENUM (
    'discovered',       -- just scraped, not yet ranked
    'ranked',           -- AI score assigned
    'queued',           -- approved for application
    'applied',          -- application submitted
    'rejected',         -- rejected by employer
    'interview',        -- interview scheduled
    'offer',            -- offer received
    'discarded'         -- manually removed from pipeline
);

-- ---------------------------------------------------------------------------
-- Enum: doc_type — generated document types
-- ---------------------------------------------------------------------------
CREATE TYPE doc_type AS ENUM (
    'cv',
    'cover_letter'
);

-- ---------------------------------------------------------------------------
-- Enum: event_type — application lifecycle events
-- ---------------------------------------------------------------------------
CREATE TYPE event_type AS ENUM (
    'applied',
    'viewed',
    'rejected',
    'interview_scheduled',
    'offer_received',
    'withdrawn'
);

-- ===========================================================================
-- TABLE: jobs
-- Raw job listings scraped from portals.
-- ===========================================================================
CREATE TABLE jobs (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    portal          portal_name     NOT NULL,
    -- Portal-specific numeric/string ID for deduplication
    external_id     TEXT,
    title           TEXT            NOT NULL,
    company         TEXT            NOT NULL,
    location        TEXT,
    modality        TEXT,           -- 'remote' | 'hybrid' | 'presencial'
    salary_min      INTEGER,        -- in currency units (see currency field)
    salary_max      INTEGER,
    currency        TEXT            DEFAULT 'CLP',
    url             TEXT            NOT NULL,
    description     TEXT,
    requirements    TEXT,
    posted_at       TIMESTAMPTZ,
    discovered_at   TIMESTAMPTZ     DEFAULT NOW(),
    status          job_status      DEFAULT 'discovered',
    -- Full raw payload from the scraper for reprocessing
    raw_json        JSONB,
    -- URL must be globally unique — prevents duplicate insertions
    CONSTRAINT jobs_url_unique UNIQUE (url)
);

-- ===========================================================================
-- TABLE: job_rankings
-- AI-generated score and analysis for each job.
-- ===========================================================================
CREATE TABLE job_rankings (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id          UUID            REFERENCES jobs(id) ON DELETE CASCADE,
    -- Score 0–100 where ≥70 is typically 'apply'
    score           INTEGER         CHECK (score >= 0 AND score <= 100),
    -- JSON: { "matched": ["Python", "FastAPI"], "missing": ["Kubernetes"] }
    skills_match    JSONB,
    recommendation  TEXT            CHECK (recommendation IN ('apply', 'skip', 'manual_review')),
    -- CV template slug that best fits this role (e.g. "backend", "fullstack")
    cv_template     TEXT,
    -- Full LLM reasoning text
    analysis        TEXT,
    ranked_at       TIMESTAMPTZ     DEFAULT NOW()
);

-- ===========================================================================
-- TABLE: documents
-- Generated CV and cover letter PDF/Markdown files.
-- ===========================================================================
CREATE TABLE documents (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id          UUID            REFERENCES jobs(id) ON DELETE SET NULL,
    type            doc_type        NOT NULL,
    filename        TEXT            NOT NULL,
    -- Absolute path inside the container (mounted from app_outputs volume)
    path            TEXT            NOT NULL,
    -- Slug of the template used for traceability
    template_used   TEXT,
    generated_at    TIMESTAMPTZ     DEFAULT NOW()
);

-- ===========================================================================
-- TABLE: applications
-- Records each job application submission.
-- ===========================================================================
CREATE TABLE applications (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id                  UUID        REFERENCES jobs(id) ON DELETE CASCADE,
    cv_doc_id               UUID        REFERENCES documents(id) ON DELETE SET NULL,
    cover_doc_id            UUID        REFERENCES documents(id) ON DELETE SET NULL,
    applied_at              TIMESTAMPTZ DEFAULT NOW(),
    status                  job_status  DEFAULT 'applied',
    -- Path to screenshot captured after successful submission
    confirmation_screenshot TEXT,
    notes                   TEXT,
    -- Set to TRUE when a human approves the application (REQUIRE_HUMAN_APPROVAL)
    human_approved          BOOLEAN     DEFAULT FALSE
);

-- ===========================================================================
-- TABLE: application_events
-- Append-only event log for each application (sourced from tracker agent).
-- ===========================================================================
CREATE TABLE application_events (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id  UUID            REFERENCES applications(id) ON DELETE CASCADE,
    event_type      event_type      NOT NULL,
    -- Arbitrary event payload (e.g. interview date, rejection reason)
    data            JSONB,
    occurred_at     TIMESTAMPTZ     DEFAULT NOW()
);

-- ===========================================================================
-- TABLE: portal_sessions
-- Stores Playwright auth state file paths per portal.
-- ===========================================================================
CREATE TABLE portal_sessions (
    portal          portal_name     PRIMARY KEY,
    -- Path to the Playwright storageState JSON file on the browser_sessions volume
    session_path    TEXT            NOT NULL,
    last_login      TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    valid           BOOLEAN         DEFAULT TRUE
);

-- ===========================================================================
-- Indexes — optimise the most frequent read patterns
-- ===========================================================================

-- Filter jobs by current status (e.g. fetch all 'queued' for apply-agent)
CREATE INDEX idx_jobs_status
    ON jobs(status);

-- Filter jobs by source portal
CREATE INDEX idx_jobs_portal
    ON jobs(portal);

-- Sort jobs by discovery time descending (dashboard feed)
CREATE INDEX idx_jobs_discovered
    ON jobs(discovered_at DESC);

-- Filter applications by status (e.g. find all active applications)
CREATE INDEX idx_applications_status
    ON applications(status);

-- Sort applications by submission time descending
CREATE INDEX idx_applications_applied
    ON applications(applied_at DESC);

-- Sort rankings by score descending (top candidates first)
CREATE INDEX idx_rankings_score
    ON job_rankings(score DESC);
