from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, Field


class BarUnit(IntEnum):
    SECOND = 1
    MINUTE = 2
    HOUR = 3
    DAY = 4
    WEEK = 5
    MONTH = 6


class Bar(BaseModel):
    """A single OHLCV bar."""

    model_config = {"populate_by_name": True}

    timestamp: datetime = Field(alias="t")
    open: float = Field(alias="o")
    high: float = Field(alias="h")
    low: float = Field(alias="l")
    close: float = Field(alias="c")
    volume: int = Field(alias="v")
