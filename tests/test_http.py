"""Tests for the async HTTP client layer."""

import httpx
import pytest

from topstep.exceptions import APIError, AuthenticationError, HTTPError, RateLimitError
from topstep.http import HTTPClient
from tests.conftest import api_response, api_error


class TestHTTPClient:
    async def test_post_success(self, mock_api):
        router, http = mock_api
        router.post("/api/test").mock(
            return_value=httpx.Response(200, json=api_response({"foo": "bar"}))
        )
        data = await http.post("/api/test", {"key": "value"})
        assert data["foo"] == "bar"

    async def test_api_error_raises(self, mock_api):
        router, http = mock_api
        router.post("/api/test").mock(
            return_value=httpx.Response(200, json=api_error(99, "Bad thing"))
        )
        with pytest.raises(APIError, match="Bad thing") as exc_info:
            await http.post("/api/test")
        assert exc_info.value.error_code == 99

    async def test_401_raises_auth_error(self, mock_api):
        router, http = mock_api
        router.post("/api/test").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        with pytest.raises(AuthenticationError):
            await http.post("/api/test")

    async def test_500_raises_http_error(self, mock_api):
        router, http = mock_api
        router.post("/api/test").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(HTTPError) as exc_info:
            await http.post("/api/test")
        assert exc_info.value.status_code == 500

    async def test_429_retries_then_raises(self, mock_api):
        router, http = mock_api
        router.post("/api/test").mock(
            return_value=httpx.Response(429, text="Too Many Requests")
        )
        with pytest.raises(RateLimitError):
            await http.post("/api/test")

    async def test_token_set_in_headers(self):
        http = HTTPClient()
        http.token = "my-token"
        assert http._client.headers["Authorization"] == "Bearer my-token"
        http.token = None
        assert "Authorization" not in http._client.headers
        await http.close()

    async def test_context_manager(self):
        async with HTTPClient() as http:
            http.token = "test"
            assert http.token == "test"
