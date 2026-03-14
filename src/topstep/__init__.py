"""TopstepX Python Client — lightweight SDK for the ProjectX Gateway API."""

from topstep.client import TopstepClient
from topstep.exceptions import (
    APIError,
    AuthenticationError,
    HTTPError,
    RateLimitError,
    TopstepError,
)
from topstep.models import (
    Account,
    Bar,
    BarUnit,
    Bracket,
    Contract,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    PlaceOrderRequest,
    Position,
    PositionType,
    Trade,
)

__version__ = "0.1.0"

__all__ = [
    "TopstepClient",
    # Exceptions
    "TopstepError",
    "AuthenticationError",
    "APIError",
    "HTTPError",
    "RateLimitError",
    # Models
    "Account",
    "Bar",
    "BarUnit",
    "Bracket",
    "Contract",
    "Order",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "PlaceOrderRequest",
    "Position",
    "PositionType",
    "Trade",
]
