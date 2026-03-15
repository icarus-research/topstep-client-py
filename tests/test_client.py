"""Tests for the top-level async client and realtime helpers."""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from topstep.client import TopstepClient
from topstep.http import HTTPClient
from topstep.realtime.market_hub import MarketHub
from topstep.realtime.user_hub import UserHub
from tests.conftest import api_response


class TestTopstepClient:
    async def test_create_closes_http_client_on_auth_failure(self):
        with respx.mock(base_url="https://api.topstepx.com") as router:
            router.post("/api/Auth/loginKey").mock(
                return_value=httpx.Response(401, text="Unauthorized")
            )

            with patch.object(HTTPClient, "close", new_callable=AsyncMock) as close_mock:
                with pytest.raises(Exception):
                    await TopstepClient.create("user@test.com", "bad-key")

                close_mock.assert_awaited_once()

    async def test_refresh_token_updates_existing_realtime_hubs(self):
        http = HTTPClient()
        http.token = "old-token"
        client = TopstepClient(http)

        client.market
        client.user

        with patch("topstep.client.auth.validate_token", new=AsyncMock(return_value="new-token")):
            await client.refresh_token()

        assert client.token == "new-token"
        assert client.market._token == "new-token"
        assert client.user._token == "new-token"
        await client.close()


class TestRealtimeCallbacks:
    async def test_market_hub_dispatches_async_callbacks(self):
        hub = MarketHub("token")
        hub._loop = asyncio.get_running_loop()
        seen: list[tuple[str, tuple]] = []
        done = asyncio.Event()

        async def on_quote(*args):
            seen.append(("quote", args))
            done.set()

        hub.on_quote(on_quote)
        hub._handle_quote("CONTRACT", {"bid": 1})

        await asyncio.wait_for(done.wait(), timeout=1)
        assert seen == [("quote", ("CONTRACT", {"bid": 1}))]

    async def test_user_hub_dispatches_async_callbacks(self):
        hub = UserHub("token")
        hub._loop = asyncio.get_running_loop()
        seen: list[tuple[str, tuple]] = []
        done = asyncio.Event()

        async def on_order(*args):
            seen.append(("order", args))
            done.set()

        hub.on_order(on_order)
        hub._handle_order({"id": 42})

        await asyncio.wait_for(done.wait(), timeout=1)
        assert seen == [("order", ({"id": 42},))]

    async def test_market_hub_restores_active_subscriptions(self):
        class FakeHub:
            def __init__(self):
                self.sent: list[tuple[str, list[str]]] = []

            def send(self, method, args):
                self.sent.append((method, args))

        hub = MarketHub("token")
        hub._hub = FakeHub()
        hub._subscriptions = {
            ("SubscribeContractQuotes", ("CONTRACT-1",)),
            ("SubscribeContractTrades", ("CONTRACT-1",)),
        }

        await hub._restore_subscriptions()

        assert hub._hub.sent == [
            ("SubscribeContractQuotes", ["CONTRACT-1"]),
            ("SubscribeContractTrades", ["CONTRACT-1"]),
        ]

    async def test_user_hub_restores_active_subscriptions(self):
        class FakeHub:
            def __init__(self):
                self.sent: list[tuple[str, list[int]]] = []

            def send(self, method, args):
                self.sent.append((method, args))

        hub = UserHub("token")
        hub._hub = FakeHub()
        hub._subscriptions = {
            ("SubscribeAccounts", ()),
            ("SubscribeOrders", (123,)),
        }

        await hub._restore_subscriptions()

        assert hub._hub.sent == [
            ("SubscribeAccounts", []),
            ("SubscribeOrders", [123]),
        ]
