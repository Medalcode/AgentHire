import pytest
from unittest.mock import patch, MagicMock
from agents.core.db import execute, fetch_all

@pytest.mark.asyncio
async def test_db_execute():
    with patch("agents.core.db.get_connection") as mock_conn:
        mock_conn.return_value.__aenter__.return_value.execute = MagicMock()
        await execute("SELECT 1")
        mock_conn.return_value.__aenter__.return_value.execute.assert_called_once_with("SELECT 1")
