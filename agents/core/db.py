"""
agents/core/db.py
=================
Async PostgreSQL client for all AgentHire agents.

Uses asyncpg for high-performance async/await PostgreSQL access.
A module-level connection pool is created on first use and reused for the
lifetime of the process (singleton pattern).

Environment variable:
    DATABASE_URL — asyncpg-compatible DSN, e.g.
        postgresql+asyncpg://user:pass@postgres:5432/agenthire

Usage:
    from agents.core.db import fetch_one, fetch_all, execute, execute_many

    job = await fetch_one("SELECT * FROM jobs WHERE id = $1", job_id)
    rows = await fetch_all("SELECT * FROM jobs WHERE status = $1", "queued")
    await execute("UPDATE jobs SET status=$1 WHERE id=$2", "ranked", job_id)
"""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

import asyncpg
from loguru import logger


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# asyncpg uses postgresql:// scheme (not postgresql+asyncpg://)
_RAW_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql://agenthire:changeme@postgres:5432/agenthire",
).replace("postgresql+asyncpg://", "postgresql://").replace("postgres+asyncpg://", "postgresql://")

_MIN_POOL_SIZE: int = int(os.environ.get("DB_POOL_MIN", "2"))
_MAX_POOL_SIZE: int = int(os.environ.get("DB_POOL_MAX", "10"))

# ---------------------------------------------------------------------------
# Singleton pool
# ---------------------------------------------------------------------------

_pool: Optional[asyncpg.Pool] = None
_pool_lock: asyncio.Lock = asyncio.Lock()


async def get_pool() -> asyncpg.Pool:
    """
    Return (and lazily create) the module-level asyncpg connection pool.

    Thread-safe: uses an asyncio Lock to prevent double initialisation.
    """
    global _pool

    if _pool is not None:
        return _pool

    async with _pool_lock:
        # Double-check inside the lock
        if _pool is not None:
            return _pool

        logger.info(
            "Creating asyncpg pool: min={} max={} dsn={}",
            _MIN_POOL_SIZE,
            _MAX_POOL_SIZE,
            _RAW_URL.rsplit("@", 1)[-1],  # log host/db only, not credentials
        )
        _pool = await asyncpg.create_pool(
            dsn=_RAW_URL,
            min_size=_MIN_POOL_SIZE,
            max_size=_MAX_POOL_SIZE,
            command_timeout=30,
            # Decode JSON columns automatically
            init=_init_connection,
        )

    return _pool


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Per-connection initialisation: register JSON codec."""
    import json

    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def close_pool() -> None:
    """Gracefully close the pool. Call on application shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("asyncpg pool closed.")


# ---------------------------------------------------------------------------
# Context manager for single-connection use (transactions, etc.)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Async context manager that acquires a connection from the pool.

    Example:
        async with get_connection() as conn:
            async with conn.transaction():
                await conn.execute("INSERT INTO jobs ...")
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

async def fetch_one(
    query: str,
    *args: Any,
) -> Optional[asyncpg.Record]:
    """
    Execute a SELECT query and return the first row, or None if no rows found.

    Args:
        query: Parameterised SQL query using $1, $2, ... placeholders.
        *args: Positional values for query parameters.

    Returns:
        asyncpg.Record (dict-like) or None.

    Example:
        row = await fetch_one("SELECT * FROM jobs WHERE id = $1", job_id)
        if row:
            print(row["title"])
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        logger.debug("fetch_one: query={} args={} found={}", query[:60], args, row is not None)
        return row


async def fetch_all(
    query: str,
    *args: Any,
) -> list[asyncpg.Record]:
    """
    Execute a SELECT query and return all matching rows.

    Args:
        query: Parameterised SQL query.
        *args: Positional values.

    Returns:
        List of asyncpg.Record objects (may be empty).

    Example:
        rows = await fetch_all(
            "SELECT * FROM jobs WHERE status = $1 ORDER BY discovered_at DESC LIMIT $2",
            "queued", 50,
        )
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        logger.debug("fetch_all: query={} args={} rows={}", query[:60], args, len(rows))
        return rows


async def execute(
    query: str,
    *args: Any,
) -> str:
    """
    Execute a DML statement (INSERT, UPDATE, DELETE) and return the status tag.

    Args:
        query: Parameterised SQL statement.
        *args: Positional values.

    Returns:
        PostgreSQL command tag, e.g. "UPDATE 1".

    Example:
        tag = await execute(
            "UPDATE jobs SET status = $1 WHERE id = $2",
            "ranked", job_id,
        )
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(query, *args)
        logger.debug("execute: query={} args={} result={}", query[:60], args, result)
        return result


async def execute_many(
    query: str,
    args_list: list[tuple[Any, ...]],
) -> None:
    """
    Execute a DML statement for multiple parameter sets (bulk insert/update).

    Uses asyncpg's executemany which pipelines all statements in one round-trip.

    Args:
        query:     Parameterised SQL statement.
        args_list: List of tuples, one per row.

    Example:
        await execute_many(
            "INSERT INTO jobs (title, company, url, portal) VALUES ($1, $2, $3, $4)",
            [("Dev", "Acme", "https://...", "linkedin"), ...],
        )
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(query, args_list)
        logger.debug("execute_many: query={} batches={}", query[:60], len(args_list))


async def fetch_val(
    query: str,
    *args: Any,
) -> Any:
    """
    Execute a query and return the first column of the first row.

    Useful for COUNT(*), MAX(), and similar scalar queries.

    Example:
        total = await fetch_val("SELECT COUNT(*) FROM jobs WHERE status = $1", "applied")
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)
