"""Tests for authentication."""

import httpx
import pytest
import respx

from topstep import auth
from topstep.exceptions import APIError, AuthenticationError
from topstep.http import HTTPClient
from tests.conftest import api_response, api_error


class TestLoginKey:
    async def test_successful_login(self):
        with respx.mock(base_url="https://api.topstepx.com") as router:
            router.post("/api/Auth/loginKey").mock(
                return_value=httpx.Response(200, json=api_response({"token": "abc123"}))
            )
            http = HTTPClient()
            token = await auth.login_key(http, "user@test.com", "key123")
            assert token == "abc123"
            await http.close()

    async def test_login_api_error(self):
        with respx.mock(base_url="https://api.topstepx.com") as router:
            router.post("/api/Auth/loginKey").mock(
                return_value=httpx.Response(200, json=api_error(1, "Invalid credentials"))
            )
            http = HTTPClient()
            with pytest.raises(APIError, match="Invalid credentials"):
                await auth.login_key(http, "bad@test.com", "wrong")
            await http.close()

    async def test_login_http_401(self):
        with respx.mock(base_url="https://api.topstepx.com") as router:
            router.post("/api/Auth/loginKey").mock(
                return_value=httpx.Response(401, text="Unauthorized")
            )
            http = HTTPClient()
            with pytest.raises(AuthenticationError):
                await auth.login_key(http, "user@test.com", "key")
            await http.close()


class TestValidateToken:
    async def test_refresh_returns_new_token(self, mock_api):
        router, http = mock_api
        router.post("/api/Auth/validate").mock(
            return_value=httpx.Response(200, json=api_response({"newToken": "refreshed"}))
        )
        result = await auth.validate_token(http)
        assert result == "refreshed"
