import pytest
import os
import asyncio
from agents.core.db import execute, fetch_one, fetch_all, fetch_val, get_pool, close_pool
import uuid

# Aseguramos que los tests corran contra PostgreSQL local usando el pool de la app
pytestmark = pytest.mark.asyncio(scope="module")

@pytest.fixture(autouse=True, scope="module")
async def setup_teardown_db():
    # Inicializa el pool
    await get_pool()
    yield
    # Limpia datos de prueba
    await execute("DELETE FROM jobs WHERE title LIKE 'TEST_JOB_%'")
    await close_pool()

async def test_db_insert_and_fetch():
    """Prueba que podemos insertar un Job en Postgres y recuperarlo."""
    ext_id = f"TEST_JOB_{uuid.uuid4()}"
    title = f"TEST_JOB_TITLE"
    url = f"https://example.com/test/{ext_id}"
    
    # Insert
    tag = await execute(
        "INSERT INTO jobs (portal, external_id, title, company, url) VALUES ($1, $2, $3, $4, $5)",
        "linkedin", ext_id, title, "Test Corp", url
    )
    assert "INSERT" in tag

    # Fetch One
    row = await fetch_one("SELECT * FROM jobs WHERE external_id = $1", ext_id)
    assert row is not None
    assert row["title"] == title
    assert row["portal"] == "linkedin"

    # Fetch Val
    count = await fetch_val("SELECT COUNT(*) FROM jobs WHERE external_id = $1", ext_id)
    assert count == 1

    # Fetch All
    rows = await fetch_all("SELECT * FROM jobs WHERE external_id = $1", ext_id)
    assert len(rows) == 1
    assert rows[0]["company"] == "Test Corp"
