"""Tests for options trading endpoints."""

from unittest.mock import MagicMock

from tests.conftest import (
    make_mock_option_contract,
    make_mock_option_snapshot,
    make_mock_order,
    make_mock_quote,
)


# --- Option Contracts ---


def test_get_option_contracts(client, mock_trading_client):
    contracts_resp = MagicMock()
    contracts_resp.model_dump.return_value = {
        "option_contracts": [
            make_mock_option_contract().model_dump.return_value,
            make_mock_option_contract(symbol="AAPL250117P00150000", type="put").model_dump.return_value,
        ],
        "next_page_token": None,
    }
    mock_trading_client.get_option_contracts.return_value = contracts_resp

    resp = client.get("/options/contracts", params={
        "underlying_symbols": "AAPL",
        "type": "call",
        "expiration_date": "2025-01-17",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "option_contracts" in data
    mock_trading_client.get_option_contracts.assert_called_once()


def test_get_option_contract_by_symbol(client, mock_trading_client):
    mock_trading_client.get_option_contract.return_value = make_mock_option_contract()

    resp = client.get("/options/contracts/AAPL250117C00150000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL250117C00150000"
    assert data["type"] == "call"
    mock_trading_client.get_option_contract.assert_called_once_with("AAPL250117C00150000")


# --- Option Chain ---


def test_get_option_chain(client, mock_option_data_client):
    chain_data = {
        "AAPL250117C00150000": make_mock_option_snapshot().model_dump.return_value,
        "AAPL250117P00150000": make_mock_option_snapshot(
            greeks={"delta": -0.45, "gamma": 0.03, "theta": -0.04, "vega": 0.15, "rho": -0.02}
        ).model_dump.return_value,
    }
    mock_option_data_client.get_option_chain.return_value = chain_data

    resp = client.get("/options/chain/AAPL", params={
        "type": "call",
        "strike_price_gte": 140.0,
        "strike_price_lte": 160.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "AAPL250117C00150000" in data
    mock_option_data_client.get_option_chain.assert_called_once()


# --- Option Quotes ---


def test_get_option_quote(client, mock_option_data_client):
    mock_quote = make_mock_quote(ask_price=5.60, bid_price=5.40)
    symbol = "AAPL250117C00150000"
    mock_option_data_client.get_option_latest_quote.return_value = {symbol: mock_quote}

    resp = client.get(f"/options/quotes/{symbol}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ask_price"] == 5.60
    assert data["bid_price"] == 5.40


# --- Option Snapshots ---


def test_get_option_snapshot(client, mock_option_data_client):
    symbol = "AAPL250117C00150000"
    mock_option_data_client.get_option_snapshot.return_value = {
        symbol: make_mock_option_snapshot(),
    }

    resp = client.get(f"/options/snapshots/{symbol}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["implied_volatility"] == 0.25
    assert data["greeks"]["delta"] == 0.55


# --- Option Orders ---


def test_submit_option_order_market(client, mock_trading_client):
    mock_trading_client.submit_order.return_value = make_mock_order(
        symbol="AAPL250117C00150000", type="market"
    )

    resp = client.post("/options/orders", json={
        "symbol": "AAPL250117C00150000",
        "qty": 1,
        "side": "buy",
        "type": "market",
        "position_intent": "buy_to_open",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL250117C00150000"
    mock_trading_client.submit_order.assert_called_once()


def test_submit_option_order_limit(client, mock_trading_client):
    mock_trading_client.submit_order.return_value = make_mock_order(
        symbol="AAPL250117C00150000", type="limit"
    )

    resp = client.post("/options/orders", json={
        "symbol": "AAPL250117C00150000",
        "qty": 1,
        "side": "buy",
        "type": "limit",
        "limit_price": 5.50,
        "position_intent": "buy_to_open",
    })
    assert resp.status_code == 200
    mock_trading_client.submit_order.assert_called_once()


def test_submit_option_order_missing_limit_price(client, mock_trading_client):
    resp = client.post("/options/orders", json={
        "symbol": "AAPL250117C00150000",
        "qty": 1,
        "side": "buy",
        "type": "limit",
        "position_intent": "buy_to_open",
    })
    assert resp.status_code == 400
    assert "limit_price" in resp.json()["detail"]


# --- Multi-Leg Orders ---


def test_submit_multi_leg_order(client, mock_trading_client):
    mock_trading_client.submit_order.return_value = make_mock_order(
        symbol=None, type="limit", order_class="mleg"
    )

    resp = client.post("/options/orders/multi-leg", json={
        "qty": 1,
        "type": "limit",
        "limit_price": 1.50,
        "legs": [
            {"symbol": "AAPL250117C00150000", "ratio_qty": 1.0, "side": "buy"},
            {"symbol": "AAPL250117C00160000", "ratio_qty": 1.0, "side": "sell"},
        ],
    })
    assert resp.status_code == 200
    mock_trading_client.submit_order.assert_called_once()


def test_submit_multi_leg_order_too_many_legs(client, mock_trading_client):
    resp = client.post("/options/orders/multi-leg", json={
        "qty": 1,
        "type": "limit",
        "limit_price": 1.50,
        "legs": [
            {"symbol": f"LEG{i}", "ratio_qty": 1.0, "side": "buy"}
            for i in range(5)
        ],
    })
    assert resp.status_code == 400
    assert "4 legs" in resp.json()["detail"]


def test_submit_multi_leg_order_too_few_legs(client, mock_trading_client):
    resp = client.post("/options/orders/multi-leg", json={
        "qty": 1,
        "type": "limit",
        "limit_price": 1.50,
        "legs": [
            {"symbol": "AAPL250117C00150000", "ratio_qty": 1.0, "side": "buy"},
        ],
    })
    assert resp.status_code == 400
    assert "2 legs" in resp.json()["detail"]


# --- Exercise ---


def test_exercise_option(client, mock_trading_client):
    mock_trading_client.exercise_options_position.return_value = None

    resp = client.post("/options/exercise/AAPL250117C00150000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "exercised"
    assert data["symbol_or_id"] == "AAPL250117C00150000"
    mock_trading_client.exercise_options_position.assert_called_once_with("AAPL250117C00150000")
