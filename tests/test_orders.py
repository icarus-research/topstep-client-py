"""Tests for orders endpoint."""

import httpx

from topstep.endpoints.orders import OrdersEndpoint
from topstep.models.order import (
    Bracket,
    Order,
    OrderSide,
    OrderType,
    PlaceOrderRequest,
)
from tests.conftest import api_response


class TestPlaceOrder:
    def test_place_returns_order_id(self, mock_api):
        router, http = mock_api
        router.post("/api/Order/place").mock(
            return_value=httpx.Response(200, json=api_response({"orderId": 42}))
        )

        endpoint = OrdersEndpoint(http)
        order_req = PlaceOrderRequest(
            account_id=1,
            contract_id="CON.F.US.ENQ.H25",
            type=OrderType.STOP,
            side=OrderSide.BUY,
            size=2,
            stop_price=4500.0,
            stop_loss_bracket=Bracket(ticks=-20, type=4),
            take_profit_bracket=Bracket(ticks=40, type=1),
        )
        order_id = endpoint.place(order_req)
        assert order_id == 42

    def test_place_order_serialization(self):
        order = PlaceOrderRequest(
            account_id=1,
            contract_id="CON.F.US.ENQ.H25",
            type=OrderType.MARKET,
            side=OrderSide.BUY,
            size=1,
        )
        d = order.to_api_dict()
        # Should use camelCase keys
        assert "accountId" in d
        assert "contractId" in d
        # Should exclude None fields
        assert "limitPrice" not in d
        assert "stopLossBracket" not in d


class TestSearchOpen:
    def test_returns_open_orders(self, mock_api):
        router, http = mock_api
        router.post("/api/Order/searchOpen").mock(
            return_value=httpx.Response(200, json=api_response({
                "orders": [{
                    "id": 10,
                    "accountId": 1,
                    "contractId": "CON.F.US.ENQ.H25",
                    "symbolId": "F.US.ENQ",
                    "creationTimestamp": "2026-03-14T14:30:00Z",
                    "updateTimestamp": "2026-03-14T14:30:00Z",
                    "status": 1,
                    "type": 4,
                    "side": 0,
                    "size": 2,
                    "stopPrice": 4500.0,
                    "fillVolume": 0,
                }]
            }))
        )

        endpoint = OrdersEndpoint(http)
        orders = endpoint.search_open(account_id=1)
        assert len(orders) == 1
        assert isinstance(orders[0], Order)
        assert orders[0].status == 1
        assert orders[0].side == OrderSide.BUY


class TestCancelOrder:
    def test_cancel_succeeds(self, mock_api):
        router, http = mock_api
        router.post("/api/Order/cancel").mock(
            return_value=httpx.Response(200, json=api_response())
        )

        endpoint = OrdersEndpoint(http)
        endpoint.cancel(account_id=1, order_id=42)  # Should not raise
