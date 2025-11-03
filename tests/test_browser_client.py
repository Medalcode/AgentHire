import pytest
from unittest.mock import patch, AsyncMock
from agents.core.browser_client import BrowserClient

@pytest.fixture
def mock_httpx():
    with patch("agents.core.browser_client.httpx.AsyncClient") as mock:
        client_instance = AsyncMock()
        mock.return_value.__aenter__.return_value = client_instance
        yield client_instance

@pytest.mark.asyncio
async def test_browser_client_open_url(mock_httpx):
    mock_httpx.post.return_value.status_code = 200
    mock_httpx.post.return_value.json = lambda: {"result": {"status": "ok"}}
    
    client = BrowserClient()
    result = await client.open_url("https://example.com")
    
    assert result["status"] == "ok"
    mock_httpx.post.assert_called_once()
    args, kwargs = mock_httpx.post.call_args
    assert kwargs["json"]["method"] == "open_url"
    assert kwargs["json"]["params"]["url"] == "https://example.com"
