# Alpaca Paper Trading API

FastAPI wrapper for Alpaca paper trading API.

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Create a `.env` file with your Alpaca API keys:
```
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
```

Get your paper trading keys from [Alpaca](https://app.alpaca.markets/paper/dashboard/overview).

3. Run the server:
```bash
uv run uvicorn alpaca_api.main:app --reload
```

4. Open http://localhost:8000/docs for interactive API documentation.

## Endpoints

### Account & Market

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/account` | Get account info |
| GET | `/clock` | Get market status |

### Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/orders` | Submit order |
| GET | `/orders` | List orders (query: `status=open\|closed\|all`) |
| GET | `/orders/{id}` | Get order by ID |
| DELETE | `/orders/{id}` | Cancel order |
| DELETE | `/orders` | Cancel all orders |

### Positions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/positions` | List all positions |
| GET | `/positions/{symbol}` | Get position by symbol |
| DELETE | `/positions/{symbol}` | Close position |

### Market Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/quotes/{symbol}` | Get latest quote |

## Examples

### Submit a market order

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "qty": 1, "side": "buy", "type": "market", "time_in_force": "day"}'
```

### Submit a limit order

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "qty": 1, "side": "buy", "type": "limit", "time_in_force": "gtc", "limit_price": 150.00}'
```

### Get account info

```bash
curl http://localhost:8000/account
```

### List open orders

```bash
curl http://localhost:8000/orders
```

### Get latest quote

```bash
curl http://localhost:8000/quotes/AAPL
```

### Close a position

```bash
curl -X DELETE http://localhost:8000/positions/AAPL
```

## Order Types

- `market` - Market order
- `limit` - Limit order (requires `limit_price`)
- `stop` - Stop order (requires `stop_price`)
- `stop_limit` - Stop limit order (requires `limit_price` and `stop_price`)
- `trailing_stop` - Trailing stop order (requires `trail_price` or `trail_percent`)

## Time in Force

- `day` - Day order
- `gtc` - Good til cancelled
- `opg` - Market on open
- `cls` - Market on close
- `ioc` - Immediate or cancel
- `fok` - Fill or kill
