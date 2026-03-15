"""Market Hub — real-time quotes, trades, and market depth via SignalR."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from signalrcore.hub_connection_builder import HubConnectionBuilder

from topstep.http import WS_MARKET_HUB

logger = logging.getLogger("topstep.realtime.market")

# Callback type: receives (contract_id, data_dict)
MarketCallback = Callable[..., None]


class MarketHub:
    """Real-time market data via the ProjectX SignalR Market Hub.

    Provides streaming quotes, trade executions, and DOM depth updates.

    Usage::

        async with await TopstepClient.create(...) as client:
            client.market.on_quote(my_quote_handler)
            client.market.connect()
            client.market.subscribe_quotes("CON.F.US.ENQ.H26")
    """

    def __init__(self, token: str, hub_url: str = WS_MARKET_HUB) -> None:
        self._token = token
        self._hub_url = hub_url
        self._hub: Any = None
        self._subscriptions: list[tuple[str, list[str]]] = []

        # User callbacks
        self._on_quote: MarketCallback | None = None
        self._on_trade: MarketCallback | None = None
        self._on_depth: MarketCallback | None = None
        self._on_open: Callable[[], None] | None = None
        self._on_close: Callable[[], None] | None = None

    def on_quote(self, callback: MarketCallback) -> None:
        """Register a handler for GatewayQuote events."""
        self._on_quote = callback

    def on_trade(self, callback: MarketCallback) -> None:
        """Register a handler for GatewayTrade events."""
        self._on_trade = callback

    def on_depth(self, callback: MarketCallback) -> None:
        """Register a handler for GatewayDepth events."""
        self._on_depth = callback

    def on_open(self, callback: Callable[[], None]) -> None:
        """Register a handler called when the WebSocket connection opens."""
        self._on_open = callback

    def on_close(self, callback: Callable[[], None]) -> None:
        """Register a handler called when the WebSocket connection closes."""
        self._on_close = callback

    def connect(self) -> None:
        """Build and start the SignalR connection.

        This is a blocking call — the connection runs in a background thread
        managed by signalrcore. Call ``stop()`` to disconnect.
        """
        url = f"{self._hub_url}?access_token={self._token}"

        self._hub = (
            HubConnectionBuilder()
            .with_url(url, options={
                "transport": "websockets",
                "skip_negotiation": True,
                "verify_ssl": True,
            })
            .configure_logging(logging.WARNING)
            .build()
        )

        # Wire up SignalR events to user callbacks
        self._hub.on("GatewayQuote", self._handle_quote)
        self._hub.on("GatewayTrade", self._handle_trade)
        self._hub.on("GatewayDepth", self._handle_depth)

        self._hub.on_open(self._handle_open)
        self._hub.on_close(self._handle_close)

        logger.info("Connecting to Market Hub...")
        self._hub.start()

    def stop(self) -> None:
        """Disconnect from the Market Hub."""
        if self._hub is not None:
            self._hub.stop()
            self._hub = None
            self._subscriptions.clear()
            logger.info("Market Hub disconnected")

    # --- Subscription management ---

    def subscribe_quotes(self, contract_id: str) -> None:
        """Subscribe to real-time quotes for a contract."""
        self._send("SubscribeContractQuotes", contract_id)

    def unsubscribe_quotes(self, contract_id: str) -> None:
        """Unsubscribe from quotes for a contract."""
        self._send("UnsubscribeContractQuotes", contract_id)

    def subscribe_trades(self, contract_id: str) -> None:
        """Subscribe to real-time trade executions for a contract."""
        self._send("SubscribeContractTrades", contract_id)

    def unsubscribe_trades(self, contract_id: str) -> None:
        """Unsubscribe from trade executions for a contract."""
        self._send("UnsubscribeContractTrades", contract_id)

    def subscribe_depth(self, contract_id: str) -> None:
        """Subscribe to real-time market depth (DOM) for a contract."""
        self._send("SubscribeContractMarketDepth", contract_id)

    def unsubscribe_depth(self, contract_id: str) -> None:
        """Unsubscribe from market depth for a contract."""
        self._send("UnsubscribeContractMarketDepth", contract_id)

    def subscribe_all(self, contract_id: str) -> None:
        """Subscribe to quotes, trades, and depth for a contract."""
        self.subscribe_quotes(contract_id)
        self.subscribe_trades(contract_id)
        self.subscribe_depth(contract_id)

    def unsubscribe_all(self, contract_id: str) -> None:
        """Unsubscribe from all streams for a contract."""
        self.unsubscribe_quotes(contract_id)
        self.unsubscribe_trades(contract_id)
        self.unsubscribe_depth(contract_id)

    # --- Internal handlers ---

    def _send(self, method: str, contract_id: str) -> None:
        if self._hub is None:
            raise RuntimeError("Not connected — call connect() first")
        self._hub.send(method, [contract_id])
        self._subscriptions.append((method, [contract_id]))
        logger.debug("Sent %s(%s)", method, contract_id)

    def _handle_quote(self, *args: Any) -> None:
        if self._on_quote:
            self._on_quote(*args)

    def _handle_trade(self, *args: Any) -> None:
        if self._on_trade:
            self._on_trade(*args)

    def _handle_depth(self, *args: Any) -> None:
        if self._on_depth:
            self._on_depth(*args)

    def _handle_open(self) -> None:
        logger.info("Market Hub connected")
        if self._on_open:
            self._on_open()

    def _handle_close(self) -> None:
        logger.info("Market Hub disconnected")
        if self._on_close:
            self._on_close()
