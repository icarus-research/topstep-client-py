"""Shared test fixtures."""

import pytest
import httpx
import respx

from topstep.http import HTTPClient


# Standard successful API envelope
def api_response(data: dict | None = None) -> dict:
    """Build a standard API success response."""
    base = {"success": True, "errorCode": 0, "errorMessage": None}
    if data:
        base.update(data)
    return base


def api_error(code: int = -1, message: str = "Something went wrong") -> dict:
    """Build a standard API error response."""
    return {"success": False, "errorCode": code, "errorMessage": message}


@pytest.fixture
async def mock_api():
    """Provide a respx mock router and a pre-authenticated async HTTPClient."""
    with respx.mock(base_url="https://api.topstepx.com") as router:
        client = HTTPClient(base_url="https://api.topstepx.com")
        client.token = "test-token-123"
        yield router, client
        await client.close()
