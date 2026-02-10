"""Shared pytest fixtures with mocked Alpaca clients."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_trading_client():
    """Create a mock TradingClient."""
    return MagicMock()


@pytest.fixture
def mock_data_client():
    """Create a mock StockHistoricalDataClient."""
    return MagicMock()


@pytest.fixture
def mock_option_data_client():
    """Create a mock OptionHistoricalDataClient."""
    return MagicMock()


@pytest.fixture
def client(mock_trading_client, mock_data_client, mock_option_data_client):
    """FastAPI TestClient with all Alpaca clients mocked."""
    with (
        patch("alpaca_api.main.get_trading_client", return_value=mock_trading_client),
        patch("alpaca_api.main.get_data_client", return_value=mock_data_client),
        patch("alpaca_api.main.get_option_data_client", return_value=mock_option_data_client),
    ):
        from alpaca_api.main import app

        yield TestClient(app)


def make_mock_order(**overrides):
    """Build a mock order response object."""
    defaults = {
        "id": "order-123",
        "client_order_id": "client-1",
        "symbol": "AAPL",
        "qty": "10",
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
        "status": "accepted",
    }
    defaults.update(overrides)
    obj = MagicMock()
    obj.model_dump.return_value = defaults
    return obj


def make_mock_position(**overrides):
    """Build a mock position response object."""
    defaults = {
        "asset_id": "asset-1",
        "symbol": "AAPL",
        "qty": "10",
        "side": "long",
        "market_value": "1500.00",
        "avg_entry_price": "150.00",
    }
    defaults.update(overrides)
    obj = MagicMock()
    obj.model_dump.return_value = defaults
    return obj


def make_mock_account(**overrides):
    """Build a mock account response object."""
    defaults = {
        "id": "account-1",
        "account_number": "PA123",
        "status": "ACTIVE",
        "buying_power": "100000.00",
        "cash": "50000.00",
        "equity": "100000.00",
    }
    defaults.update(overrides)
    obj = MagicMock()
    obj.model_dump.return_value = defaults
    return obj


def make_mock_clock(**overrides):
    """Build a mock clock response object."""
    defaults = {
        "timestamp": "2025-01-15T10:00:00-05:00",
        "is_open": True,
        "next_open": "2025-01-16T09:30:00-05:00",
        "next_close": "2025-01-15T16:00:00-05:00",
    }
    defaults.update(overrides)
    obj = MagicMock()
    obj.model_dump.return_value = defaults
    return obj


def make_mock_quote(**overrides):
    """Build a mock quote response object."""
    defaults = {
        "ask_price": 150.50,
        "ask_size": 200,
        "bid_price": 150.25,
        "bid_size": 300,
        "timestamp": "2025-01-15T10:00:00Z",
    }
    defaults.update(overrides)
    obj = MagicMock()
    obj.model_dump.return_value = defaults
    return obj


def make_mock_option_contract(**overrides):
    """Build a mock option contract response object."""
    defaults = {
        "id": "contract-1",
        "symbol": "AAPL250117C00150000",
        "name": "AAPL Jan 17 2025 150 Call",
        "status": "active",
        "tradable": True,
        "expiration_date": "2025-01-17",
        "root_symbol": "AAPL",
        "underlying_symbol": "AAPL",
        "type": "call",
        "style": "american",
        "strike_price": "150.00",
        "size": "100",
    }
    defaults.update(overrides)
    obj = MagicMock()
    obj.model_dump.return_value = defaults
    return obj


def make_mock_option_snapshot(**overrides):
    """Build a mock option snapshot response object."""
    defaults = {
        "latest_trade": {"price": 5.50, "size": 10, "timestamp": "2025-01-15T10:00:00Z"},
        "latest_quote": {"ask_price": 5.60, "bid_price": 5.40, "timestamp": "2025-01-15T10:00:00Z"},
        "greeks": {"delta": 0.55, "gamma": 0.03, "theta": -0.05, "vega": 0.15, "rho": 0.02},
        "implied_volatility": 0.25,
    }
    defaults.update(overrides)
    obj = MagicMock()
    obj.model_dump.return_value = defaults
    return obj
