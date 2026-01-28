"""Pydantic request/response models."""

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class OrderSide(str, Enum):
    """Order side."""

    buy = "buy"
    sell = "sell"


class OrderType(str, Enum):
    """Order type."""

    market = "market"
    limit = "limit"
    stop = "stop"
    stop_limit = "stop_limit"
    trailing_stop = "trailing_stop"


class TimeInForce(str, Enum):
    """Time in force."""

    day = "day"
    gtc = "gtc"
    opg = "opg"
    cls = "cls"
    ioc = "ioc"
    fok = "fok"


class OrderRequest(BaseModel):
    """Request model for submitting an order."""

    symbol: str
    qty: Decimal | None = None
    notional: Decimal | None = None
    side: OrderSide
    type: OrderType
    time_in_force: TimeInForce = TimeInForce.day
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    trail_price: Decimal | None = None
    trail_percent: Decimal | None = None
    extended_hours: bool = False
    client_order_id: str | None = None


class ClosePositionRequest(BaseModel):
    """Request model for closing a position."""

    qty: Decimal | None = None
    percentage: Decimal | None = None
