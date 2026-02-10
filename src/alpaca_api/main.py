"""FastAPI application with Alpaca paper trading endpoints."""

from functools import lru_cache
from typing import Any

from alpaca.data import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.requests import (
    OptionChainRequest as AlpacaOptionChainRequest,
    OptionLatestQuoteRequest,
    OptionSnapshotRequest,
    StockLatestQuoteRequest,
)
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import (
    ContractType as AlpacaContractType,
    ExerciseStyle as AlpacaExerciseStyle,
    OrderClass as AlpacaOrderClass,
    OrderSide,
    OrderType,
    PositionIntent as AlpacaPositionIntent,
    TimeInForce,
)
from alpaca.trading.requests import (
    GetOptionContractsRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    OptionLegRequest,
    StopLimitOrderRequest,
    StopOrderRequest,
    TrailingStopOrderRequest,
)
from fastapi import FastAPI, HTTPException

from alpaca_api.config import get_settings
from alpaca_api.models import (
    ClosePositionRequest,
    MultiLegOrderRequest,
    OptionOrderRequest,
    OrderRequest,
)

app = FastAPI(
    title="Alpaca Paper Trading API",
    description="FastAPI wrapper for Alpaca paper trading",
    version="0.1.0",
)


@lru_cache
def get_trading_client() -> TradingClient:
    """Get cached trading client instance."""
    settings = get_settings()
    return TradingClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        paper=True,
    )


@lru_cache
def get_data_client() -> StockHistoricalDataClient:
    """Get cached data client instance."""
    settings = get_settings()
    return StockHistoricalDataClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
    )


@lru_cache
def get_option_data_client() -> OptionHistoricalDataClient:
    """Get cached option data client instance."""
    settings = get_settings()
    return OptionHistoricalDataClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
    )


def serialize_alpaca_response(obj: Any) -> dict | list | Any:
    """Convert Alpaca objects to JSON-serializable dicts."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dict__"):
        return {k: serialize_alpaca_response(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [serialize_alpaca_response(item) for item in obj]
    if isinstance(obj, dict):
        return {k: serialize_alpaca_response(v) for k, v in obj.items()}
    return obj


# Health check
@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


# Account
@app.get("/account")
def get_account() -> dict:
    """Get account information."""
    account = get_trading_client().get_account()
    return serialize_alpaca_response(account)


# Clock
@app.get("/clock")
def get_clock() -> dict:
    """Get market clock status."""
    clock = get_trading_client().get_clock()
    return serialize_alpaca_response(clock)


# Orders
@app.post("/orders")
def submit_order(order: OrderRequest) -> dict:
    """Submit a new order."""
    side = OrderSide.BUY if order.side.value == "buy" else OrderSide.SELL
    tif = TimeInForce(order.time_in_force.value)

    order_request: MarketOrderRequest | LimitOrderRequest | StopOrderRequest | StopLimitOrderRequest | TrailingStopOrderRequest

    if order.type.value == "market":
        order_request = MarketOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            notional=order.notional,
            side=side,
            time_in_force=tif,
            extended_hours=order.extended_hours,
            client_order_id=order.client_order_id,
        )
    elif order.type.value == "limit":
        if order.limit_price is None:
            raise HTTPException(status_code=400, detail="limit_price required for limit orders")
        order_request = LimitOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            notional=order.notional,
            side=side,
            time_in_force=tif,
            limit_price=order.limit_price,
            extended_hours=order.extended_hours,
            client_order_id=order.client_order_id,
        )
    elif order.type.value == "stop":
        if order.stop_price is None:
            raise HTTPException(status_code=400, detail="stop_price required for stop orders")
        order_request = StopOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            notional=order.notional,
            side=side,
            time_in_force=tif,
            stop_price=order.stop_price,
            extended_hours=order.extended_hours,
            client_order_id=order.client_order_id,
        )
    elif order.type.value == "stop_limit":
        if order.limit_price is None or order.stop_price is None:
            raise HTTPException(
                status_code=400,
                detail="limit_price and stop_price required for stop_limit orders",
            )
        order_request = StopLimitOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            side=side,
            time_in_force=tif,
            limit_price=order.limit_price,
            stop_price=order.stop_price,
            extended_hours=order.extended_hours,
            client_order_id=order.client_order_id,
        )
    elif order.type.value == "trailing_stop":
        order_request = TrailingStopOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            side=side,
            time_in_force=tif,
            trail_price=order.trail_price,
            trail_percent=order.trail_percent,
            extended_hours=order.extended_hours,
            client_order_id=order.client_order_id,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported order type: {order.type}")

    result = get_trading_client().submit_order(order_request)
    return serialize_alpaca_response(result)


@app.get("/orders")
def list_orders(status: str = "open") -> list:
    """List orders."""
    from alpaca.trading.enums import QueryOrderStatus
    from alpaca.trading.requests import GetOrdersRequest

    query_status = QueryOrderStatus(status)
    request = GetOrdersRequest(status=query_status)
    orders = get_trading_client().get_orders(filter=request)
    return serialize_alpaca_response(orders)


@app.get("/orders/{order_id}")
def get_order(order_id: str) -> dict:
    """Get a specific order by ID."""
    order = get_trading_client().get_order_by_id(order_id)
    return serialize_alpaca_response(order)


@app.delete("/orders/{order_id}")
def cancel_order(order_id: str) -> dict:
    """Cancel a specific order."""
    get_trading_client().cancel_order_by_id(order_id)
    return {"status": "cancelled", "order_id": order_id}


@app.delete("/orders")
def cancel_all_orders() -> dict:
    """Cancel all open orders."""
    result = get_trading_client().cancel_orders()
    return {"status": "cancelled", "cancelled": serialize_alpaca_response(result)}


# Positions
@app.get("/positions")
def list_positions() -> list:
    """List all positions."""
    positions = get_trading_client().get_all_positions()
    return serialize_alpaca_response(positions)


@app.get("/positions/{symbol}")
def get_position(symbol: str) -> dict:
    """Get position for a specific symbol."""
    position = get_trading_client().get_open_position(symbol)
    return serialize_alpaca_response(position)


@app.delete("/positions/{symbol}")
def close_position(symbol: str, request: ClosePositionRequest | None = None) -> dict:
    """Close a position for a specific symbol."""
    from alpaca.trading.requests import ClosePositionRequest as AlpacaCloseRequest

    close_request = None
    if request and (request.qty or request.percentage):
        close_request = AlpacaCloseRequest(
            qty=str(request.qty) if request.qty else None,
            percentage=str(request.percentage) if request.percentage else None,
        )

    result = get_trading_client().close_position(symbol, close_options=close_request)
    return serialize_alpaca_response(result)


# Quotes
@app.get("/quotes/{symbol}")
def get_quote(symbol: str) -> dict:
    """Get the latest quote for a symbol."""
    request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
    quotes = get_data_client().get_stock_latest_quote(request)
    return serialize_alpaca_response(quotes.get(symbol))


# ====================== Options Endpoints ======================


@app.get("/options/contracts")
def get_option_contracts(
    underlying_symbols: str | None = None,
    expiration_date: str | None = None,
    expiration_date_gte: str | None = None,
    expiration_date_lte: str | None = None,
    root_symbol: str | None = None,
    type: str | None = None,
    style: str | None = None,
    strike_price_gte: str | None = None,
    strike_price_lte: str | None = None,
    limit: int | None = None,
    page_token: str | None = None,
) -> dict:
    """List option contracts with optional filters."""
    params: dict[str, Any] = {}

    if underlying_symbols:
        params["underlying_symbols"] = [s.strip() for s in underlying_symbols.split(",")]
    if expiration_date:
        params["expiration_date"] = expiration_date
    if expiration_date_gte:
        params["expiration_date_gte"] = expiration_date_gte
    if expiration_date_lte:
        params["expiration_date_lte"] = expiration_date_lte
    if root_symbol:
        params["root_symbol"] = root_symbol
    if type:
        params["type"] = AlpacaContractType(type)
    if style:
        params["style"] = AlpacaExerciseStyle(style)
    if strike_price_gte:
        params["strike_price_gte"] = strike_price_gte
    if strike_price_lte:
        params["strike_price_lte"] = strike_price_lte
    if limit is not None:
        params["limit"] = limit
    if page_token:
        params["page_token"] = page_token

    request = GetOptionContractsRequest(**params)
    result = get_trading_client().get_option_contracts(request)
    return serialize_alpaca_response(result)


@app.get("/options/contracts/{symbol_or_id}")
def get_option_contract(symbol_or_id: str) -> dict:
    """Get a single option contract by symbol or ID."""
    result = get_trading_client().get_option_contract(symbol_or_id)
    return serialize_alpaca_response(result)


@app.get("/options/chain/{underlying_symbol}")
def get_option_chain(
    underlying_symbol: str,
    type: str | None = None,
    strike_price_gte: float | None = None,
    strike_price_lte: float | None = None,
    expiration_date: str | None = None,
    expiration_date_gte: str | None = None,
    expiration_date_lte: str | None = None,
    root_symbol: str | None = None,
) -> dict:
    """Get option chain (snapshots with greeks/IV) for an underlying symbol."""
    params: dict[str, Any] = {"underlying_symbol": underlying_symbol}

    if type:
        params["type"] = AlpacaContractType(type)
    if strike_price_gte is not None:
        params["strike_price_gte"] = strike_price_gte
    if strike_price_lte is not None:
        params["strike_price_lte"] = strike_price_lte
    if expiration_date:
        params["expiration_date"] = expiration_date
    if expiration_date_gte:
        params["expiration_date_gte"] = expiration_date_gte
    if expiration_date_lte:
        params["expiration_date_lte"] = expiration_date_lte
    if root_symbol:
        params["root_symbol"] = root_symbol

    request = AlpacaOptionChainRequest(**params)
    result = get_option_data_client().get_option_chain(request)
    return serialize_alpaca_response(result)


@app.get("/options/quotes/{symbol}")
def get_option_quote(symbol: str) -> dict:
    """Get latest quote for an option contract."""
    request = OptionLatestQuoteRequest(symbol_or_symbols=symbol)
    quotes = get_option_data_client().get_option_latest_quote(request)
    return serialize_alpaca_response(quotes.get(symbol))


@app.get("/options/snapshots/{symbol}")
def get_option_snapshot(symbol: str) -> dict:
    """Get snapshot (quote + trade + greeks + IV) for an option contract."""
    request = OptionSnapshotRequest(symbol_or_symbols=symbol)
    snapshots = get_option_data_client().get_option_snapshot(request)
    return serialize_alpaca_response(snapshots.get(symbol))


@app.post("/options/orders")
def submit_option_order(order: OptionOrderRequest) -> dict:
    """Submit a single-leg option order."""
    side = OrderSide.BUY if order.side.value == "buy" else OrderSide.SELL
    tif = TimeInForce(order.time_in_force.value)
    order_type = OrderType(order.type.value)

    position_intent = None
    if order.position_intent:
        position_intent = AlpacaPositionIntent(order.position_intent.value)

    if order_type == OrderType.MARKET:
        alpaca_request = MarketOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            side=side,
            time_in_force=tif,
            position_intent=position_intent,
        )
    elif order_type == OrderType.LIMIT:
        if order.limit_price is None:
            raise HTTPException(status_code=400, detail="limit_price required for limit orders")
        alpaca_request = LimitOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            side=side,
            time_in_force=tif,
            limit_price=order.limit_price,
            position_intent=position_intent,
        )
    elif order_type == OrderType.STOP:
        if order.stop_price is None:
            raise HTTPException(status_code=400, detail="stop_price required for stop orders")
        alpaca_request = StopOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            side=side,
            time_in_force=tif,
            stop_price=order.stop_price,
            position_intent=position_intent,
        )
    elif order_type == OrderType.STOP_LIMIT:
        if order.limit_price is None or order.stop_price is None:
            raise HTTPException(
                status_code=400,
                detail="limit_price and stop_price required for stop_limit orders",
            )
        alpaca_request = StopLimitOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            side=side,
            time_in_force=tif,
            limit_price=order.limit_price,
            stop_price=order.stop_price,
            position_intent=position_intent,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported order type for options: {order.type}")

    result = get_trading_client().submit_order(alpaca_request)
    return serialize_alpaca_response(result)


@app.post("/options/orders/multi-leg")
def submit_multi_leg_order(order: MultiLegOrderRequest) -> dict:
    """Submit a multi-leg option order (spreads, straddles, etc.)."""
    if len(order.legs) < 2:
        raise HTTPException(status_code=400, detail="At least 2 legs are required for multi-leg orders")
    if len(order.legs) > 4:
        raise HTTPException(status_code=400, detail="At most 4 legs are allowed for multi-leg orders")

    tif = TimeInForce(order.time_in_force.value)
    order_type = OrderType(order.type.value)

    legs = []
    for leg in order.legs:
        leg_side = OrderSide(leg.side.value) if leg.side else None
        leg_intent = AlpacaPositionIntent(leg.position_intent.value) if leg.position_intent else None
        legs.append(OptionLegRequest(
            symbol=leg.symbol,
            ratio_qty=leg.ratio_qty,
            side=leg_side,
            position_intent=leg_intent,
        ))

    if order_type == OrderType.LIMIT:
        if order.limit_price is None:
            raise HTTPException(status_code=400, detail="limit_price required for limit orders")
        alpaca_request = LimitOrderRequest(
            qty=order.qty,
            time_in_force=tif,
            limit_price=order.limit_price,
            order_class=AlpacaOrderClass.MLEG,
            legs=legs,
        )
    elif order_type == OrderType.MARKET:
        alpaca_request = MarketOrderRequest(
            qty=order.qty,
            time_in_force=tif,
            order_class=AlpacaOrderClass.MLEG,
            legs=legs,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported order type for multi-leg: {order.type}")

    result = get_trading_client().submit_order(alpaca_request)
    return serialize_alpaca_response(result)


@app.post("/options/exercise/{symbol_or_id}")
def exercise_option(symbol_or_id: str) -> dict:
    """Exercise a held option contract."""
    get_trading_client().exercise_options_position(symbol_or_id)
    return {"status": "exercised", "symbol_or_id": symbol_or_id}
