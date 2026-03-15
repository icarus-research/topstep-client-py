"""Authentication and token management."""

from __future__ import annotations

from topstep.exceptions import AuthenticationError
from topstep.http import HTTPClient


async def login_key(http: HTTPClient, username: str, api_key: str) -> str:
    """Authenticate with username + API key. Returns the session token."""
    data = await http.post("/api/Auth/loginKey", {
        "userName": username,
        "apiKey": api_key,
    })

    token = data.get("token")
    if not token:
        raise AuthenticationError("Login succeeded but no token returned")

    return token


async def login_app(
    http: HTTPClient,
    username: str,
    password: str,
    device_id: str,
    app_id: str,
    verify_key: str,
) -> str:
    """Authenticate as an authorized application. Returns the session token."""
    data = await http.post("/api/Auth/loginApp", {
        "userName": username,
        "password": password,
        "deviceId": device_id,
        "appId": app_id,
        "verifyKey": verify_key,
    })

    token = data.get("token")
    if not token:
        raise AuthenticationError("Login succeeded but no token returned")

    return token


async def validate_token(http: HTTPClient) -> str | None:
    """Validate the current token and return a refreshed one if available."""
    data = await http.post("/api/Auth/validate")
    return data.get("newToken") or data.get("token")
