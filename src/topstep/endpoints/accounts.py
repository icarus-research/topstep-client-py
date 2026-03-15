from __future__ import annotations

from topstep.http import HTTPClient
from topstep.models.account import Account


class AccountsEndpoint:
    """Operations on trading accounts."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    async def search(self, only_active: bool = True) -> list[Account]:
        """Search accounts. By default returns only active accounts."""
        data = await self._http.post("/api/Account/search", {
            "onlyActiveAccounts": only_active,
        })
        return [Account.model_validate(a) for a in data.get("accounts", [])]
