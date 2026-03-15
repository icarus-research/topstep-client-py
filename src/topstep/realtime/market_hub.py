"""Market Hub — real-time quotes, trades, and market depth via SignalR."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable
from typing import Any

from signalrcore.hub_connection_builder import HubConnectionBuilder

from topstep.http import WS_MARKET_HUB

logger = logging.getLogger("topstep.realtime.market")

# Callback type: receives (contract_id, data_dict)
MarketCallback = Callable[..., Any]


class MarketHub:
    """Real-time market data via the ProjectX SignalR Market Hub.

    Provides streaming quotes, trade executions, and DOM depth updates.

    Usage::

        async with await TopstepClient.create(...) as client:
            client.market.on_quote(my_quote_handler)
            await client.market.connect()
            await client.market.subscribe_quotes("CON.F.US.ENQ.H26")
    """

    def __init__(self, token: str, hub_url: str = WS_MARKET_HUB) -> None:
        self._token = token
        self._hub_url = hub_url
        self._hub: Any = None
        self._subscriptions: set[tuple[str, tuple[str, ...]]] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._connected = False

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

    def set_token(self, token: str) -> None:
        """Update the auth token used for future connections."""
        self._token = token

    async def connect(self) -> None:
        """Build and start the SignalR connection without blocking the event loop.

        SignalR itself runs its own background thread. This method only waits
        for the initial connection startup to complete.
        """
        if self._connected:
            return

        self._loop = asyncio.get_running_loop()
        self._hub = (
            HubConnectionBuilder()
            .with_url(self._hub_url, options={
                "access_token_factory": lambda: self._token,
                "verify_ssl": True,
            })
            .configure_logging(logging.WARNING)
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_attempts": 0,
            })
            .build()
        )

        # Wire up SignalR events to user callbacks
        self._hub.on("GatewayQuote", self._handle_quote)
        self._hub.on("GatewayTrade", self._handle_trade)
        self._hub.on("GatewayDepth", self._handle_depth)

        self._hub.on_open(self._handle_open)
        self._hub.on_close(self._handle_close)

        logger.info("Connecting to Market Hub...")
        try:
            await asyncio.to_thread(self._hub.start)
        except Exception:
            self._hub = None
            self._connected = False
            raise

        self._connected = True

    async def stop(self) -> None:
        """Disconnect from the Market Hub."""
        if self._hub is not None:
            try:
                await asyncio.to_thread(self._hub.stop)
            finally:
                self._hub = None
                self._subscriptions.clear()
                self._connected = False
                logger.info("Market Hub disconnected")

    # --- Subscription management ---

    async def subscribe_quotes(self, contract_id: str) -> None:
        """Subscribe to real-time quotes for a contract."""
        await self._send("SubscribeContractQuotes", contract_id)
        self._subscriptions.add(("SubscribeContractQuotes", (contract_id,)))

    async def unsubscribe_quotes(self, contract_id: str) -> None:
        """Unsubscribe from quotes for a contract."""
        await self._send("UnsubscribeContractQuotes", contract_id)
        self._subscriptions.discard(("SubscribeContractQuotes", (contract_id,)))

    async def subscribe_trades(self, contract_id: str) -> None:
        """Subscribe to real-time trade executions for a contract."""
        await self._send("SubscribeContractTrades", contract_id)
        self._subscriptions.add(("SubscribeContractTrades", (contract_id,)))

    async def unsubscribe_trades(self, contract_id: str) -> None:
        """Unsubscribe from trade executions for a contract."""
        await self._send("UnsubscribeContractTrades", contract_id)
        self._subscriptions.discard(("SubscribeContractTrades", (contract_id,)))

    async def subscribe_depth(self, contract_id: str) -> None:
        """Subscribe to real-time market depth (DOM) for a contract."""
        await self._send("SubscribeContractMarketDepth", contract_id)
        self._subscriptions.add(("SubscribeContractMarketDepth", (contract_id,)))

    async def unsubscribe_depth(self, contract_id: str) -> None:
        """Unsubscribe from market depth for a contract."""
        await self._send("UnsubscribeContractMarketDepth", contract_id)
        self._subscriptions.discard(("SubscribeContractMarketDepth", (contract_id,)))

    async def subscribe_all(self, contract_id: str) -> None:
        """Subscribe to quotes, trades, and depth for a contract."""
        await self.subscribe_quotes(contract_id)
        await self.subscribe_trades(contract_id)
        await self.subscribe_depth(contract_id)

    async def unsubscribe_all(self, contract_id: str) -> None:
        """Unsubscribe from all streams for a contract."""
        await self.unsubscribe_quotes(contract_id)
        await self.unsubscribe_trades(contract_id)
        await self.unsubscribe_depth(contract_id)

    # --- Internal handlers ---

    async def _send(self, method: str, contract_id: str) -> None:
        if self._hub is None:
            raise RuntimeError("Not connected — call connect() first")
        await asyncio.to_thread(self._hub.send, method, [contract_id])
        logger.debug("Sent %s(%s)", method, contract_id)

    async def _restore_subscriptions(self) -> None:
        if self._hub is None:
            return

        for method, args in sorted(self._subscriptions):
            await asyncio.to_thread(self._hub.send, method, list(args))
            logger.debug("Restored %s(%s)", method, args)

    def _dispatch_callback(self, callback: Callable[..., Any] | None, *args: Any) -> None:
        if callback is None:
            return

        loop = self._loop
        if loop is None or loop.is_closed():
            logger.warning("Dropping realtime callback because no active event loop is available")
            return

        def runner() -> None:
            try:
                result = callback(*args)
                if inspect.isawaitable(result):
                    task = loop.create_task(result)
                    task.add_done_callback(self._log_task_error)
            except Exception:
                logger.exception("Unhandled exception in market callback")

        loop.call_soon_threadsafe(runner)

    def _log_task_error(self, task: asyncio.Task[Any]) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("Unhandled exception in async market callback")

    def _handle_quote(self, *args: Any) -> None:
        self._dispatch_callback(self._on_quote, *args)

    def _handle_trade(self, *args: Any) -> None:
        self._dispatch_callback(self._on_trade, *args)

    def _handle_depth(self, *args: Any) -> None:
        self._dispatch_callback(self._on_depth, *args)

    def _handle_open(self) -> None:
        logger.info("Market Hub connected")
        if self._subscriptions and self._loop is not None and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(
                lambda: self._loop.create_task(self._restore_subscriptions())
            )
        self._dispatch_callback(self._on_open)

    def _handle_close(self) -> None:
        logger.info("Market Hub disconnected")
        self._connected = False
        self._dispatch_callback(self._on_close)
