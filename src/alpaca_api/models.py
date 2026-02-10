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


class ContractType(str, Enum):
    """Option contract type."""

    call = "call"
    put = "put"


class ExerciseStyle(str, Enum):
    """Option exercise style."""

    american = "american"
    european = "european"


class PositionIntent(str, Enum):
    """Position intent for option orders."""

    buy_to_open = "buy_to_open"
    buy_to_close = "buy_to_close"
    sell_to_open = "sell_to_open"
    sell_to_close = "sell_to_close"


class OrderClass(str, Enum):
    """Order class."""

    simple = "simple"
    mleg = "mleg"


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


# --- Options models ---


class OptionContractsRequest(BaseModel):
    """Request model for querying option contracts."""

    underlying_symbols: list[str] | None = None
    expiration_date: str | None = None
    expiration_date_gte: str | None = None
    expiration_date_lte: str | None = None
    root_symbol: str | None = None
    type: ContractType | None = None
    style: ExerciseStyle | None = None
    strike_price_gte: str | None = None
    strike_price_lte: str | None = None
    limit: int | None = None
    page_token: str | None = None


class OptionChainRequest(BaseModel):
    """Request model for querying an option chain."""

    underlying_symbol: str
    type: ContractType | None = None
    strike_price_gte: float | None = None
    strike_price_lte: float | None = None
    expiration_date: str | None = None
    expiration_date_gte: str | None = None
    expiration_date_lte: str | None = None
    root_symbol: str | None = None


class OptionOrderRequest(BaseModel):
    """Request model for submitting a single-leg option order."""

    symbol: str
    qty: int
    side: OrderSide
    type: OrderType
    time_in_force: TimeInForce = TimeInForce.day
    position_intent: PositionIntent | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None


class OptionLeg(BaseModel):
    """Leg definition for multi-leg option orders."""

    symbol: str
    ratio_qty: float
    side: OrderSide | None = None
    position_intent: PositionIntent | None = None


class MultiLegOrderRequest(BaseModel):
    """Request model for submitting a multi-leg option order."""

    qty: int
    type: OrderType
    time_in_force: TimeInForce = TimeInForce.day
    legs: list[OptionLeg]
    limit_price: Decimal | None = None
