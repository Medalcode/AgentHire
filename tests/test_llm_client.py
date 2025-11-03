import pytest
from unittest.mock import patch, AsyncMock
from agents.core.llm_client import complete_json

@pytest.mark.asyncio
async def test_llm_complete_json():
    with patch("agents.core.llm_client.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock()
        mock_client.chat.completions.create.return_value.choices = [
            type('obj', (object,), {"message": type('obj', (object,), {"content": '{"status":"ok"}'})})
        ]
        result = await complete_json("test prompt", "test system")
        assert result == {"status": "ok"}
