"""Tests for the HTTP client layer."""

import httpx
import pytest
import respx

from topstep.exceptions import APIError, AuthenticationError, HTTPError, RateLimitError
from topstep.http import HTTPClient
from tests.conftest import api_response, api_error


class TestHTTPClient:
    def test_post_success(self, mock_api):
        router, http = mock_api
        router.post("/api/test").mock(
            return_value=httpx.Response(200, json=api_response({"foo": "bar"}))
        )
        data = http.post("/api/test", {"key": "value"})
        assert data["foo"] == "bar"

    def test_api_error_raises(self, mock_api):
        router, http = mock_api
        router.post("/api/test").mock(
            return_value=httpx.Response(200, json=api_error(99, "Bad thing"))
        )
        with pytest.raises(APIError, match="Bad thing") as exc_info:
            http.post("/api/test")
        assert exc_info.value.error_code == 99

    def test_401_raises_auth_error(self, mock_api):
        router, http = mock_api
        router.post("/api/test").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        with pytest.raises(AuthenticationError):
            http.post("/api/test")

    def test_500_raises_http_error(self, mock_api):
        router, http = mock_api
        router.post("/api/test").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(HTTPError) as exc_info:
            http.post("/api/test")
        assert exc_info.value.status_code == 500

    def test_429_retries_then_raises(self, mock_api):
        router, http = mock_api
        router.post("/api/test").mock(
            return_value=httpx.Response(429, text="Too Many Requests")
        )
        with pytest.raises(RateLimitError):
            http.post("/api/test")

    def test_token_set_in_headers(self):
        http = HTTPClient()
        http.token = "my-token"
        assert http._client.headers["Authorization"] == "Bearer my-token"
        http.token = None
        assert "Authorization" not in http._client.headers
        http.close()

    def test_context_manager(self):
        with HTTPClient() as http:
            http.token = "test"
            assert http.token == "test"
