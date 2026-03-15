# topstep-client-py

[![CI](https://github.com/icarus-research/topstep-client-py/actions/workflows/ci.yml/badge.svg)](https://github.com/icarus-research/topstep-client-py/actions/workflows/ci.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/topstep-client-py)](https://pypi.org/project/topstep-client-py/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/topstep-client-py)](https://pypi.org/project/topstep-client-py/)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Async](https://img.shields.io/badge/async-native-brightgreen.svg)](#topstep-client-py)

Lightweight async Python client for the [TopstepX](https://www.topstep.com/) / [ProjectX Gateway API](https://gateway.docs.projectx.com/docs/intro/).

## Disclaimer

This project is an independent community-built library. It is not officially affiliated with, endorsed by, maintained by, or otherwise directly associated with Topstep, TopstepX, or ProjectX.

The goal of this package is to provide a clean and practical Python client for the public API and realtime interfaces. It is maintained on a best-effort basis and will be kept up to date as quickly as reasonably possible when the upstream API changes.

This repository only provides the API client layer. It does not include trading strategies, alpha generation, signal logic, backtesting frameworks, portfolio tooling, or other trader-specific systems. Those decisions and tools are intentionally left to each user and their own workflow.

- Async-first (built on `httpx`)
- Fully typed responses with Pydantic models
- All 16 REST endpoints covered
- Real-time market & user data via SignalR WebSocket
- Retry with backoff + rate limit handling
- Clean exception hierarchy

## Installation

```bash
pip install topstep-client-py
```

## Quick Start

```python
import asyncio
from datetime import datetime, timedelta, timezone
from topstep import TopstepClient, BarUnit

async def main():
    async with await TopstepClient.create(
        username="you@email.com",
        api_key="your-api-key",
    ) as client:

        # Search accounts
        accounts = await client.accounts.search()
        account = accounts[0]
        print(f"Account: {account.name} | Balance: {account.balance}")

        # Find a contract
        contracts = await client.contracts.search("Micro E-mini Nasdaq")
        contract = contracts[0]
        print(f"Contract: {contract.description} | Tick: {contract.tick_size}")

        # Get historical bars
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=1)
        bars = await client.history.retrieve_bars(
            contract_id=contract.id,
            start=start,
            end=end,
            unit=BarUnit.MINUTE,
            unit_number=5,
        )
        for bar in bars[-3:]:
            print(f"  {bar.timestamp} O:{bar.open} H:{bar.high} L:{bar.low} C:{bar.close}")

asyncio.run(main())
```

## Placing Orders

```python
from topstep import PlaceOrderRequest, OrderType, OrderSide, Bracket

order_id = await client.orders.place(PlaceOrderRequest(
    account_id=account.id,
    contract_id=contract.id,
    type=OrderType.STOP,
    side=OrderSide.BUY,
    size=2,
    stop_price=21500.0,
    stop_loss_bracket=Bracket(ticks=-20, type=4),
    take_profit_bracket=Bracket(ticks=40, type=1),
))
print(f"Order placed: {order_id}")

# Check open orders
open_orders = await client.orders.search_open(account.id)

# Cancel an order
await client.orders.cancel(account.id, order_id)
```

## Positions

```python
# Get open positions
positions = await client.positions.search_open(account.id)

# Close all positions for a contract
await client.positions.close(account.id, contract.id)

# Partial close
await client.positions.partial_close(account.id, contract.id, size=1)
```

## Trade History

```python
from datetime import datetime, timezone

trades = await client.trades.search(
    account_id=account.id,
    start=datetime(2026, 3, 1, tzinfo=timezone.utc),
)
for trade in trades:
    print(f"  {trade.price} | P&L: {trade.profit_and_loss} | Fees: {trade.fees}")
```

## Real-Time Market Data (WebSocket)

```python
import asyncio
from topstep import TopstepClient

async def main():
    async with await TopstepClient.create(
        username="you@email.com",
        api_key="your-api-key",
    ) as client:

        # Register callbacks
        client.market.on_quote(lambda *args: print("QUOTE:", args))
        client.market.on_trade(lambda *args: print("TRADE:", args))
        client.market.on_depth(lambda *args: print("DEPTH:", args))

        # Connect and subscribe
        await client.market.connect()
        await client.market.subscribe_all("CON.F.US.ENQ.H26")

        # Keep alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await client.market.stop()

asyncio.run(main())
```

## Real-Time User Data (WebSocket)

```python
async with await TopstepClient.create(...) as client:

    client.user.on_order(lambda *args: print("ORDER:", args))
    client.user.on_position(lambda *args: print("POSITION:", args))
    client.user.on_trade(lambda *args: print("TRADE:", args))
    client.user.on_account(lambda *args: print("ACCOUNT:", args))

    await client.user.connect()
    await client.user.subscribe_all(account_id=account.id)

    # ...
```

## Token Refresh

Tokens expire after 24 hours. Refresh manually:

```python
await client.refresh_token()
```

## Error Handling

```python
from topstep import TopstepError, AuthenticationError, APIError, RateLimitError

try:
    accounts = await client.accounts.search()
except AuthenticationError:
    # Invalid credentials or expired token
    await client.refresh_token()
except RateLimitError:
    # HTTP 429 — too many requests (auto-retried 3 times before raising)
    pass
except APIError as e:
    # API returned success=False
    print(f"API error [{e.error_code}]: {e}")
except TopstepError:
    # Any other client error
    pass
```

## Rate Limits

The API enforces these limits (handled automatically with retry + backoff):

- `History/retrieveBars`: 50 requests per 30 seconds
- All other endpoints: 200 requests per 60 seconds

## Development

```bash
git clone https://github.com/YOUR_USER/topstep-client-py.git
cd topstep-client-py
pip install -e ".[dev]"
pytest
```
