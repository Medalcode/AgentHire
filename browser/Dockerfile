# =============================================================================
# AgentHire — browser/Dockerfile
# Builds the agent-browser MCP server image.
#
# agent-browser is an npm package that wraps Playwright and exposes a
# JSON-RPC 2.0 HTTP endpoint for browser automation.
# =============================================================================

FROM node:20-slim

# ---------------------------------------------------------------------------
# System dependencies required by Playwright / Chromium
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libxshmfence1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Install agent-browser globally
# ---------------------------------------------------------------------------
RUN npm install -g agent-browser

# ---------------------------------------------------------------------------
# Install Playwright browsers (Chromium) with system deps.
# The `|| true` prevents build failure if the script is not present on this
# version of agent-browser; the browsers may already be bundled.
# ---------------------------------------------------------------------------
RUN agent-browser install --with-deps || true

# ---------------------------------------------------------------------------
# Working directory for session persistence
# ---------------------------------------------------------------------------
WORKDIR /app
RUN mkdir -p /app/sessions

# ---------------------------------------------------------------------------
# Install express for the JSON-RPC proxy
# ---------------------------------------------------------------------------
RUN npm install express

# ---------------------------------------------------------------------------
# Copy the server script
# ---------------------------------------------------------------------------
COPY server.js /app/server.js

# ---------------------------------------------------------------------------
# Health check — the MCP server exposes /health on its port
# ---------------------------------------------------------------------------
HEALTHCHECK --interval=15s --timeout=10s --start-period=30s --retries=5 \
    CMD curl -sf http://localhost:8765/health || exit 1

# Expose the JSON-RPC 2.0 MCP server port
EXPOSE 8765

# ---------------------------------------------------------------------------
# Launch command — start the JSON-RPC proxy server
# ---------------------------------------------------------------------------
CMD ["node", "server.js"]
