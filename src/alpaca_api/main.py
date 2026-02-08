"""FastAPI application with Alpaca paper trading endpoints."""

from functools import lru_cache
from typing import Any

from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.requests import (
    LimitOrderRequest,
    MarketOrderRequest,
    StopLimitOrderRequest,
    StopOrderRequest,
    TrailingStopOrderRequest,
)
from fastapi import FastAPI, HTTPException

from alpaca_api.config import get_settings
from alpaca_api.models import ClosePositionRequest, OrderRequest

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
