"""Tests for accounts endpoint."""

import httpx
import respx

from topstep.endpoints.accounts import AccountsEndpoint
from topstep.models.account import Account
from tests.conftest import api_response


class TestAccountsSearch:
    def test_returns_accounts(self, mock_api):
        router, http = mock_api
        router.post("/api/Account/search").mock(
            return_value=httpx.Response(200, json=api_response({
                "accounts": [
                    {"id": 1, "name": "50K-Account", "balance": 50000.0,
                     "canTrade": True, "isVisible": True},
                    {"id": 2, "name": "Practice", "balance": 100000.0,
                     "canTrade": True, "isVisible": True},
                ]
            }))
        )

        endpoint = AccountsEndpoint(http)
        accounts = endpoint.search()

        assert len(accounts) == 2
        assert isinstance(accounts[0], Account)
        assert accounts[0].name == "50K-Account"
        assert accounts[0].balance == 50000.0
        assert accounts[0].can_trade is True

    def test_empty_accounts(self, mock_api):
        router, http = mock_api
        router.post("/api/Account/search").mock(
            return_value=httpx.Response(200, json=api_response({"accounts": []}))
        )

        endpoint = AccountsEndpoint(http)
        accounts = endpoint.search()
        assert accounts == []
