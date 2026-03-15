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
from topstep.realtime.market_hub import MarketHub
from topstep.realtime.user_hub import UserHub


class TopstepClient:
    """Async client for the TopstepX / ProjectX Gateway API.

    Usage::

        async with await TopstepClient.create(
            username="you@email.com",
            api_key="your-key",
        ) as client:
            accounts = await client.accounts.search()
            bars = await client.history.retrieve_bars(contract_id, start, end)
    """

    def __init__(self, http: HTTPClient) -> None:
        # Use TopstepClient.create() instead of calling __init__ directly.
        self._http = http

        # Namespaced REST endpoints
        self.accounts = AccountsEndpoint(http)
        self.contracts = ContractsEndpoint(http)
        self.history = HistoryEndpoint(http)
        self.orders = OrdersEndpoint(http)
        self.positions = PositionsEndpoint(http)
        self.trades = TradesEndpoint(http)

        # Realtime hubs (lazily connected)
        self._market_hub: MarketHub | None = None
        self._user_hub: UserHub | None = None

    @classmethod
    async def create(
        cls,
        username: str,
        api_key: str,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
    ) -> TopstepClient:
        """Create and authenticate a new client.

        This is the primary way to instantiate the client since
        authentication is an async operation.
        """
        http = HTTPClient(base_url=base_url, timeout=timeout)
        try:
            token = await auth.login_key(http, username, api_key)
        except Exception:
            await http.close()
            raise

        http.token = token
        return cls(http)

    @property
    def token(self) -> str | None:
        """Current session token."""
        return self._http.token

    async def refresh_token(self) -> None:
        """Validate and refresh the session token."""
        new_token = await auth.validate_token(self._http)
        if new_token:
            self._http.token = new_token
            if self._market_hub is not None:
                self._market_hub.set_token(new_token)
            if self._user_hub is not None:
                self._user_hub.set_token(new_token)

    @property
    def market(self) -> MarketHub:
        """Real-time market data hub (quotes, trades, depth).

        The connection is created on first access. Call
        ``await client.market.connect()`` before subscribing.
        """
        if self._market_hub is None:
            self._market_hub = MarketHub(self._http.token or "")
        return self._market_hub

    @property
    def user(self) -> UserHub:
        """Real-time user hub (accounts, orders, positions, trades).

        The connection is created on first access. Call
        ``await client.user.connect()`` before subscribing.
        """
        if self._user_hub is None:
            self._user_hub = UserHub(self._http.token or "")
        return self._user_hub

    async def close(self) -> None:
        """Close all connections (HTTP + WebSocket hubs)."""
        if self._market_hub is not None:
            await self._market_hub.stop()
        if self._user_hub is not None:
            await self._user_hub.stop()
        await self._http.close()

    async def __aenter__(self) -> TopstepClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
