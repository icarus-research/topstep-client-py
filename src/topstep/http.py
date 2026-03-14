"""Low-level HTTP client with auth headers, retry, and error handling."""

from __future__ import annotations

import time
from typing import Any

import httpx

from topstep.exceptions import APIError, AuthenticationError, HTTPError, RateLimitError

# TopstepX base URLs
BASE_URL = "https://api.topstepx.com"

# Default retry config
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds, doubles each retry


class HTTPClient:
    """Thin HTTP wrapper that handles auth headers, retries, and error parsing."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self._token: str | None = None
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    @property
    def token(self) -> str | None:
        return self._token

    @token.setter
    def token(self, value: str | None) -> None:
        self._token = value
        if value:
            self._client.headers["Authorization"] = f"Bearer {value}"
        else:
            self._client.headers.pop("Authorization", None)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a POST request with retry logic and error handling.

        Returns the parsed JSON response body (the API envelope is validated
        and stripped — callers get the raw dict to pick out domain fields).
        """
        last_exc: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.post(path, json=payload or {})
            except httpx.TimeoutException as exc:
                last_exc = HTTPError(408, f"Request timed out: {exc}")
                time.sleep(RETRY_BACKOFF * (2**attempt))
                continue
            except httpx.HTTPError as exc:
                last_exc = HTTPError(0, str(exc))
                time.sleep(RETRY_BACKOFF * (2**attempt))
                continue

            # Rate limit — wait and retry
            if response.status_code == 429:
                last_exc = RateLimitError()
                time.sleep(RETRY_BACKOFF * (2**attempt))
                continue

            # Auth failure — no point retrying
            if response.status_code == 401:
                raise AuthenticationError("Unauthorized — invalid or expired token")

            # Other HTTP errors
            if response.status_code != 200:
                raise HTTPError(response.status_code, response.text)

            # Parse JSON envelope
            data = response.json()
            if not data.get("success", False):
                error_code = data.get("errorCode", 0)
                error_msg = data.get("errorMessage") or "Unknown API error"
                raise APIError(error_msg, error_code)

            return data

        # All retries exhausted
        raise last_exc  # type: ignore[misc]

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HTTPClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
