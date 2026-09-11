-- =============================================================================
-- AgentHire — database/migrations/002_candidate_kb.sql
-- Schema for Candidate Knowledge Base (Facts)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Enum: evidence_type — source of the skill verification
-- ---------------------------------------------------------------------------
CREATE TYPE evidence_type AS ENUM (
    'EXPERIENCE',
    'PROJECT',
    'CERTIFICATION',
    'MANUAL'
);

-- ===========================================================================
-- TABLE: candidate_profiles
-- ===========================================================================
CREATE TABLE candidate_profiles (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT            NOT NULL,
    email           TEXT            NOT NULL,
    phone           TEXT,
    location        TEXT,
    linkedin_url    TEXT,
    github_url      TEXT,
    portfolio_url   TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW()
);

-- ===========================================================================
-- TABLE: candidate_experiences
-- ===========================================================================
CREATE TABLE candidate_experiences (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id    UUID            NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    company         TEXT            NOT NULL,
    role            TEXT            NOT NULL,
    location        TEXT,
    start_date      DATE            NOT NULL,
    end_date        DATE,           -- NULL means 'Present'
    modality        TEXT,           -- 'Remote', 'On-site', 'Hybrid'
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW()
);

-- ===========================================================================
-- TABLE: candidate_experience_bullets
-- ===========================================================================
CREATE TABLE candidate_experience_bullets (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    experience_id   UUID            NOT NULL REFERENCES candidate_experiences(id) ON DELETE CASCADE,
    content         TEXT            NOT NULL,
    display_order   INTEGER         DEFAULT 0,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

-- ===========================================================================
-- TABLE: candidate_projects
-- ===========================================================================
CREATE TABLE candidate_projects (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id    UUID            NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    name            TEXT            NOT NULL,
    description     TEXT            NOT NULL,
    url             TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW()
);

-- ===========================================================================
-- TABLE: candidate_education
-- ===========================================================================
CREATE TABLE candidate_education (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id    UUID            NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    institution     TEXT            NOT NULL,
    degree          TEXT            NOT NULL,
    start_date      DATE,
    end_date        DATE,
    notes           TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

-- ===========================================================================
-- TABLE: candidate_certifications
-- ===========================================================================
CREATE TABLE candidate_certifications (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id    UUID            NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    name            TEXT            NOT NULL,
    issuer          TEXT            NOT NULL,
    issue_year      INTEGER,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

-- ===========================================================================
-- TABLE: candidate_skills
-- ===========================================================================
CREATE TABLE candidate_skills (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id    UUID            NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    name            TEXT            NOT NULL,
    category        TEXT,           -- 'languages', 'frameworks', etc.
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    -- Prevent duplicate skills per candidate
    CONSTRAINT unique_candidate_skill UNIQUE (candidate_id, name)
);

-- ===========================================================================
-- TABLE: candidate_evidence
-- Uses "Exclusive Arc" nullable foreign keys instead of strict polymorphism
-- to maintain database referential integrity.
-- ===========================================================================
CREATE TABLE candidate_evidence (
    id                UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_id          UUID            NOT NULL REFERENCES candidate_skills(id) ON DELETE CASCADE,
    evidence_type     evidence_type   NOT NULL,
    
    -- Nullable foreign keys for each possible source
    experience_id     UUID            REFERENCES candidate_experiences(id) ON DELETE CASCADE,
    project_id        UUID            REFERENCES candidate_projects(id) ON DELETE CASCADE,
    certification_id  UUID            REFERENCES candidate_certifications(id) ON DELETE CASCADE,
    
    created_at        TIMESTAMPTZ     DEFAULT NOW(),

    -- Check constraint to ensure exactly one (or zero if MANUAL) FK is populated based on type
    CONSTRAINT check_exclusive_arc CHECK (
        (evidence_type = 'EXPERIENCE' AND experience_id IS NOT NULL AND project_id IS NULL AND certification_id IS NULL) OR
        (evidence_type = 'PROJECT' AND project_id IS NOT NULL AND experience_id IS NULL AND certification_id IS NULL) OR
        (evidence_type = 'CERTIFICATION' AND certification_id IS NOT NULL AND experience_id IS NULL AND project_id IS NULL) OR
        (evidence_type = 'MANUAL' AND experience_id IS NULL AND project_id IS NULL AND certification_id IS NULL)
    ),
    
    -- Prevent duplicate evidence linking the exact same skill to the exact same source
    CONSTRAINT unique_experience_evidence UNIQUE (skill_id, experience_id),
    CONSTRAINT unique_project_evidence UNIQUE (skill_id, project_id),
    CONSTRAINT unique_certification_evidence UNIQUE (skill_id, certification_id)
);

-- ===========================================================================
-- Indexes — optimise querying candidate facts
-- ===========================================================================
CREATE INDEX idx_candidate_experiences_candidate ON candidate_experiences(candidate_id);
CREATE INDEX idx_candidate_projects_candidate ON candidate_projects(candidate_id);
CREATE INDEX idx_candidate_skills_candidate ON candidate_skills(candidate_id);
CREATE INDEX idx_candidate_evidence_skill ON candidate_evidence(skill_id);
