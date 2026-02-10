"""Tests for existing stock trading endpoints."""

from unittest.mock import MagicMock

from tests.conftest import (
    make_mock_account,
    make_mock_clock,
    make_mock_order,
    make_mock_position,
    make_mock_quote,
)


# --- Health & Account ---


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


def test_get_account(client, mock_trading_client):
    mock_trading_client.get_account.return_value = make_mock_account()
    resp = client.get("/account")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACTIVE"
    assert data["buying_power"] == "100000.00"
    mock_trading_client.get_account.assert_called_once()


def test_get_clock(client, mock_trading_client):
    mock_trading_client.get_clock.return_value = make_mock_clock()
    resp = client.get("/clock")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_open"] is True
    mock_trading_client.get_clock.assert_called_once()


# --- Orders ---


def test_submit_market_order(client, mock_trading_client):
    mock_trading_client.submit_order.return_value = make_mock_order()
    resp = client.post("/orders", json={
        "symbol": "AAPL",
        "qty": 10,
        "side": "buy",
        "type": "market",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["status"] == "accepted"
    mock_trading_client.submit_order.assert_called_once()


def test_submit_limit_order(client, mock_trading_client):
    mock_trading_client.submit_order.return_value = make_mock_order(type="limit")
    resp = client.post("/orders", json={
        "symbol": "AAPL",
        "qty": 10,
        "side": "buy",
        "type": "limit",
        "limit_price": 150.00,
    })
    assert resp.status_code == 200
    mock_trading_client.submit_order.assert_called_once()


def test_submit_stop_order(client, mock_trading_client):
    mock_trading_client.submit_order.return_value = make_mock_order(type="stop")
    resp = client.post("/orders", json={
        "symbol": "AAPL",
        "qty": 10,
        "side": "sell",
        "type": "stop",
        "stop_price": 145.00,
    })
    assert resp.status_code == 200
    mock_trading_client.submit_order.assert_called_once()


def test_submit_stop_limit_order(client, mock_trading_client):
    mock_trading_client.submit_order.return_value = make_mock_order(type="stop_limit")
    resp = client.post("/orders", json={
        "symbol": "AAPL",
        "qty": 10,
        "side": "sell",
        "type": "stop_limit",
        "limit_price": 144.00,
        "stop_price": 145.00,
    })
    assert resp.status_code == 200
    mock_trading_client.submit_order.assert_called_once()


def test_submit_trailing_stop_order(client, mock_trading_client):
    mock_trading_client.submit_order.return_value = make_mock_order(type="trailing_stop")
    resp = client.post("/orders", json={
        "symbol": "AAPL",
        "qty": 10,
        "side": "sell",
        "type": "trailing_stop",
        "trail_percent": 5.0,
    })
    assert resp.status_code == 200
    mock_trading_client.submit_order.assert_called_once()


def test_submit_limit_order_missing_price(client, mock_trading_client):
    resp = client.post("/orders", json={
        "symbol": "AAPL",
        "qty": 10,
        "side": "buy",
        "type": "limit",
    })
    assert resp.status_code == 400
    assert "limit_price" in resp.json()["detail"]


def test_list_orders(client, mock_trading_client):
    mock_trading_client.get_orders.return_value = [make_mock_order(), make_mock_order(id="order-456")]
    resp = client.get("/orders")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    mock_trading_client.get_orders.assert_called_once()


def test_get_order(client, mock_trading_client):
    mock_trading_client.get_order_by_id.return_value = make_mock_order()
    resp = client.get("/orders/order-123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "order-123"
    mock_trading_client.get_order_by_id.assert_called_once_with("order-123")


def test_cancel_order(client, mock_trading_client):
    mock_trading_client.cancel_order_by_id.return_value = None
    resp = client.delete("/orders/order-123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelled"
    assert data["order_id"] == "order-123"
    mock_trading_client.cancel_order_by_id.assert_called_once_with("order-123")


def test_cancel_all_orders(client, mock_trading_client):
    mock_trading_client.cancel_orders.return_value = []
    resp = client.delete("/orders")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelled"
    mock_trading_client.cancel_orders.assert_called_once()


# --- Positions ---


def test_list_positions(client, mock_trading_client):
    mock_trading_client.get_all_positions.return_value = [
        make_mock_position(),
        make_mock_position(symbol="TSLA"),
    ]
    resp = client.get("/positions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_position(client, mock_trading_client):
    mock_trading_client.get_open_position.return_value = make_mock_position()
    resp = client.get("/positions/AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    mock_trading_client.get_open_position.assert_called_once_with("AAPL")


def test_close_position(client, mock_trading_client):
    mock_trading_client.close_position.return_value = make_mock_order(symbol="AAPL", side="sell")
    resp = client.delete("/positions/AAPL")
    assert resp.status_code == 200
    mock_trading_client.close_position.assert_called_once()


def test_close_position_partial(client, mock_trading_client):
    mock_trading_client.close_position.return_value = make_mock_order(symbol="AAPL", side="sell", qty="5")
    resp = client.request("DELETE", "/positions/AAPL", json={"qty": 5})
    assert resp.status_code == 200
    mock_trading_client.close_position.assert_called_once()
    # Verify close_options was passed
    call_kwargs = mock_trading_client.close_position.call_args
    assert call_kwargs[1]["close_options"] is not None


# --- Quotes ---


def test_get_quote(client, mock_data_client):
    mock_quote = make_mock_quote()
    mock_data_client.get_stock_latest_quote.return_value = {"AAPL": mock_quote}
    resp = client.get("/quotes/AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ask_price"] == 150.50
    assert data["bid_price"] == 150.25
