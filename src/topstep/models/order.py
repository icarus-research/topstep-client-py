from datetime import datetime
from enum import IntEnum
from typing import Optional

from pydantic import BaseModel, Field


class OrderType(IntEnum):
    UNKNOWN = 0
    LIMIT = 1
    MARKET = 2
    STOP_LIMIT = 3
    STOP = 4
    TRAILING_STOP = 5
    JOIN_BID = 6
    JOIN_ASK = 7


class OrderSide(IntEnum):
    BUY = 0
    SELL = 1


class OrderStatus(IntEnum):
    NONE = 0
    OPEN = 1
    FILLED = 2
    CANCELLED = 3
    EXPIRED = 4
    REJECTED = 5
    PENDING = 6


class Bracket(BaseModel):
    """Stop-loss or take-profit bracket attached to an order."""

    ticks: int
    type: int


class Order(BaseModel):
    """An order as returned by the API."""

    model_config = {"populate_by_name": True}

    id: int
    account_id: int = Field(alias="accountId")
    contract_id: str = Field(alias="contractId")
    symbol_id: str = Field(alias="symbolId")
    creation_timestamp: datetime = Field(alias="creationTimestamp")
    update_timestamp: datetime = Field(alias="updateTimestamp")
    status: OrderStatus
    type: OrderType
    side: OrderSide
    size: int
    limit_price: Optional[float] = Field(None, alias="limitPrice")
    stop_price: Optional[float] = Field(None, alias="stopPrice")
    filled_price: Optional[float] = Field(None, alias="filledPrice")
    fill_volume: int = Field(0, alias="fillVolume")
    custom_tag: Optional[str] = Field(None, alias="customTag")


class PlaceOrderRequest(BaseModel):
    """Payload for placing a new order."""

    model_config = {"populate_by_name": True}

    account_id: int = Field(alias="accountId")
    contract_id: str = Field(alias="contractId")
    type: OrderType
    side: OrderSide
    size: int = 1
    limit_price: Optional[float] = Field(None, alias="limitPrice")
    stop_price: Optional[float] = Field(None, alias="stopPrice")
    trail_price: Optional[float] = Field(None, alias="trailPrice")
    custom_tag: Optional[str] = Field(None, alias="customTag")
    stop_loss_bracket: Optional[Bracket] = Field(None, alias="stopLossBracket")
    take_profit_bracket: Optional[Bracket] = Field(None, alias="takeProfitBracket")

    def to_api_dict(self) -> dict:
        """Serialize to camelCase dict for the API."""
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)
