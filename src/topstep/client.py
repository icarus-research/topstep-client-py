"""TopstepX API client — the main entry point."""

from __future__ import annotations

from topstep import auth
from topstep.endpoints.accounts import AccountsEndpoint
from topstep.endpoints.contracts import ContractsEndpoint
from topstep.endpoints.history import HistoryEndpoint
from topstep.endpoints.orders import OrdersEndpoint
from topstep.endpoints.positions import PositionsEndpoint
from topstep.endpoints.trades import TradesEndpoint
from topstep.http import BASE_URL, HTTPClient


class TopstepClient:
    """Client for the TopstepX / ProjectX Gateway API.

    Usage::

        client = TopstepClient(username="you@email.com", api_key="your-key")
        accounts = client.accounts.search()
        bars = client.history.retrieve_bars(contract_id, start, end)
        client.close()

    Or as a context manager::

        with TopstepClient(username="...", api_key="...") as client:
            accounts = client.accounts.search()
    """

    def __init__(
        self,
        username: str,
        api_key: str,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self._http = HTTPClient(base_url=base_url, timeout=timeout)

        # Authenticate
        token = auth.login_key(self._http, username, api_key)
        self._http.token = token

        # Namespaced endpoints
        self.accounts = AccountsEndpoint(self._http)
        self.contracts = ContractsEndpoint(self._http)
        self.history = HistoryEndpoint(self._http)
        self.orders = OrdersEndpoint(self._http)
        self.positions = PositionsEndpoint(self._http)
        self.trades = TradesEndpoint(self._http)

    @property
    def token(self) -> str | None:
        """Current session token."""
        return self._http.token

    def refresh_token(self) -> None:
        """Validate and refresh the session token."""
        new_token = auth.validate_token(self._http)
        if new_token:
            self._http.token = new_token

    def close(self) -> None:
        """Close the underlying HTTP connection."""
        self._http.close()

    def __enter__(self) -> TopstepClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
