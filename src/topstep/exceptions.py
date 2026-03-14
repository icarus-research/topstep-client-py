"""Exception hierarchy for the TopstepX client."""


class TopstepError(Exception):
    """Base exception for all TopstepX client errors."""


class AuthenticationError(TopstepError):
    """Raised when authentication fails (invalid credentials, expired token)."""


class APIError(TopstepError):
    """Raised when the API returns success=False in its response."""

    def __init__(self, message: str, error_code: int = 0):
        self.error_code = error_code
        super().__init__(f"[{error_code}] {message}" if error_code else message)


class HTTPError(TopstepError):
    """Raised for non-200 HTTP status codes."""

    def __init__(self, status_code: int, detail: str = ""):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {detail}" if detail else f"HTTP {status_code}")


class RateLimitError(HTTPError):
    """Raised when the API returns HTTP 429 (too many requests)."""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)
