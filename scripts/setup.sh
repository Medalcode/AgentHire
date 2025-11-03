#!/usr/bin/env bash
# =============================================================================
# AgentHire — scripts/setup.sh
# First-time environment setup script.
#
# Usage:
#   chmod +x scripts/setup.sh
#   ./scripts/setup.sh
#
# What this script does:
#   1. Checks that Docker and docker compose are installed
#   2. Copies .env.example → .env if .env does not exist
#   3. Creates required local directories
#   4. Starts PostgreSQL and Redis containers
#   5. Waits for PostgreSQL to be ready
#   6. Runs the initial DB migration
#   7. Prints next steps
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Colours for output
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
die()     { error "$*"; exit 1; }

# ---------------------------------------------------------------------------
# Resolve project root (directory containing this script's parent)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

info "AgentHire project root: ${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

echo ""
echo -e "${BOLD}============================================================${NC}"
echo -e "${BOLD}  AgentHire — First-time Setup                             ${NC}"
echo -e "${BOLD}============================================================${NC}"
echo ""

# ===========================================================================
# STEP 1 — Check Docker
# ===========================================================================
info "Step 1/6 — Checking dependencies..."

if ! command -v docker &>/dev/null; then
    die "Docker is not installed. Visit https://docs.docker.com/get-docker/"
fi
success "Docker found: $(docker --version)"

# Support both 'docker compose' (v2 plugin) and 'docker-compose' (v1 standalone)
if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    die "Docker Compose is not installed. Visit https://docs.docker.com/compose/install/"
fi
success "Docker Compose found: $($COMPOSE_CMD version)"

# ===========================================================================
# STEP 2 — Create .env from .env.example
# ===========================================================================
info "Step 2/6 — Checking environment configuration..."

if [ -f ".env" ]; then
    warn ".env already exists — skipping copy. Review it to ensure all values are set."
else
    if [ ! -f ".env.example" ]; then
        die ".env.example not found. Are you running this from the project root?"
    fi
    cp .env.example .env
    success ".env created from .env.example"
    warn "⚠️  IMPORTANT: Open .env and fill in real values before proceeding!"
    echo ""
    echo -e "${YELLOW}  Required values to update:${NC}"
    echo "    - POSTGRES_PASSWORD"
    echo "    - N8N_ENCRYPTION_KEY  (run: openssl rand -hex 16)"
    echo "    - OPENAI_API_KEY or GEMINI_API_KEY"
    echo "    - Portal credentials (LINKEDIN_EMAIL, LINKEDIN_PASSWORD, etc.)"
    echo ""
    read -r -p "Press ENTER once you have filled in .env, or Ctrl+C to exit..."
fi

# Load env vars for use in this script
set -a
# shellcheck disable=SC1091
source .env
set +a

# Validate critical variables
: "${POSTGRES_USER:?POSTGRES_USER is not set in .env}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is not set in .env}"
: "${POSTGRES_DB:?POSTGRES_DB is not set in .env}"

success "Environment loaded. DB=${POSTGRES_DB}, USER=${POSTGRES_USER}"

# ===========================================================================
# STEP 3 — Create required directories
# ===========================================================================
info "Step 3/6 — Creating required directories..."

DIRS=(
    "outputs"
    "browser/sessions"
    "n8n/workflows"
    "database/migrations"
    "logs"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "${dir}" ]; then
        mkdir -p "${dir}"
        success "Created: ${dir}/"
    else
        info "Already exists: ${dir}/"
    fi
done

# ===========================================================================
# STEP 4 — Start PostgreSQL and Redis
# ===========================================================================
info "Step 4/6 — Starting PostgreSQL and Redis..."

$COMPOSE_CMD up -d postgres redis

success "PostgreSQL and Redis containers started."

# ===========================================================================
# STEP 5 — Wait for PostgreSQL to be ready
# ===========================================================================
info "Step 5/6 — Waiting for PostgreSQL to be ready..."

MAX_WAIT=60   # seconds
ELAPSED=0
INTERVAL=3

echo -n "  Waiting"
while ! $COMPOSE_CMD exec -T postgres \
        pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -q 2>/dev/null; do

    if [ "${ELAPSED}" -ge "${MAX_WAIT}" ]; then
        echo ""
        die "PostgreSQL did not become ready within ${MAX_WAIT}s. Check: $COMPOSE_CMD logs postgres"
    fi

    echo -n "."
    sleep "${INTERVAL}"
    ELAPSED=$((ELAPSED + INTERVAL))
done
echo ""
success "PostgreSQL is ready (waited ${ELAPSED}s)."

# ===========================================================================
# STEP 6 — Run database migration
# ===========================================================================
info "Step 6/6 — Running initial database migration..."

MIGRATION_FILE="database/migrations/001_init.sql"

if [ ! -f "${MIGRATION_FILE}" ]; then
    die "Migration file not found: ${MIGRATION_FILE}"
fi

# The migration file is mounted into the container at /migrations/
$COMPOSE_CMD exec -T postgres \
    psql \
    --username="${POSTGRES_USER}" \
    --dbname="${POSTGRES_DB}" \
    --file="/migrations/001_init.sql" \
    --echo-errors

success "Migration applied: ${MIGRATION_FILE}"

# ===========================================================================
# Done — Print next steps
# ===========================================================================
echo ""
echo -e "${BOLD}============================================================${NC}"
echo -e "${GREEN}${BOLD}  ✅  AgentHire setup complete!${NC}"
echo -e "${BOLD}============================================================${NC}"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo ""
echo "  1. Build and start all agent services:"
echo -e "     ${CYAN}$COMPOSE_CMD up -d --build${NC}"
echo ""
echo "  2. Start with dashboard (dev mode):"
echo -e "     ${CYAN}$COMPOSE_CMD --profile dev up -d --build${NC}"
echo ""
echo "  3. Open n8n workflow editor:"
echo -e "     ${CYAN}http://localhost:5679${NC}"
echo ""
echo "  4. Open dashboard:"
echo -e "     ${CYAN}http://localhost:3000${NC}"
echo ""
echo "  5. Check agent logs:"
echo -e "     ${CYAN}$COMPOSE_CMD logs -f agent-discovery${NC}"
echo ""
echo -e "${YELLOW}Tip:${NC} All agents expose a /health endpoint:"
echo "  http://localhost:8001/health  (discovery)"
echo "  http://localhost:8002/health  (ranking)"
echo "  http://localhost:8003/health  (cv-generator)"
echo "  http://localhost:8004/health  (cover-letter)"
echo "  http://localhost:8005/health  (apply)"
echo "  http://localhost:8006/health  (tracker)"
echo "  http://localhost:8007/health  (profile-updater)"
echo ""
