# Binance Futures Testnet Trading Bot

A Python trading bot for the Binance USD-M Futures Testnet. Started as a simple script to sign requests and place orders, and grew into a full CLI + dashboard setup.

What it does:
- Validates every order before it ever reaches Binance
- CLI menu for placing orders and checking history
- A small Flask API behind a browser dashboard
- Handles MARKET, LIMIT, and STOP (stop-limit) orders
- Lets you download order history as JSON or CSV

---

## Project Structure

```
binance/
├── requirements.txt
├── README.md
├── frontend/                  # Browser dashboard (HTML + JS)
│   ├── index.html             # Dashboard page
│   ├── client-info.html       # Account balance & info
│   ├── orders.html            # Place orders form
│   ├── history.html           # Order history with download
│   ├── styles.css
│   └── app.js                 # Talks to the Flask server
│
└── trading_bot/               # Python backend
    ├── .env                   # API keys (never commit this)
    ├── client.py              # Signing + requests to Binance
    ├── validation.py          # Checks input before it hits the API
    ├── orders.py              # Order placement (CLI)
    ├── history.py             # Fetch & show order history (CLI)
    ├── cli.py                 # Interactive menu
    ├── server.py              # Flask API for the frontend
    └── order_log.py           # Local logging (optional)
```

---

## Before You Start

- You'll need a Binance Futures **Testnet** account — sign up at [testnet.binancefuture.com](https://testnet.binancefuture.com).
- Generate a Testnet API key and secret from the Testnet dashboard. These are separate from your real Binance keys, so don't mix them up.
- Python 3.9+.
- Everything here runs against the Testnet only — no real funds involved.
- Heads up: the Testnet itself is occasionally flaky. The client retries automatically (up to 5 times) if a request times out.

---

## Setup

Clone/navigate into the project:

```bash
cd binance
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Add your keys in `trading_bot/.env`:

```env
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

Double check these are from testnet.binancefuture.com, not the live site — mixing them up is a common gotcha.

---

## Running It

### Option A — CLI

From the `trading_bot` folder:

```bash
cd trading_bot
python cli.py
```

You'll get a menu:

```
=== Binance Futures Testnet CLI ===
1. Account details
2. Place order
3. Live API order history
4. Exit
```

**Placing a MARKET order:**
```
Select an option: 2
Symbol (e.g. BTCUSDT): BTCUSDT
Side (BUY/SELL): BUY
Order type (MARKET/LIMIT/STOP): MARKET
Quantity: 0.001
```

**Placing a STOP order:**
```
Select an option: 2
Symbol (e.g. BTCUSDT): BTCUSDT
Side (BUY/SELL): SELL
Order type (MARKET/LIMIT/STOP): STOP
Quantity: 0.005
Price (execution limit): 60000
Time in force (GTC/IOC/FOK): GTC
Stop price (trigger): 60500
```
This SELL STOP fires once price drops to 60500, then places a limit sell at 60000.

**Checking history:**
```
Select an option: 3
Symbol to check (e.g. BTCUSDT): BTCUSDT
```

---

### Option B — Dashboard

Start the Flask server:

```bash
cd trading_bot
python server.py
```

You should see something like:
```
Starting Binance Bot API server on http://127.0.0.1:5000
* Running on http://127.0.0.1:5000
```

Then just open `binance/frontend/index.html` in your browser — Chrome, Edge, Firefox, whatever you've got.

| Page | What's there |
|---|---|
| Dashboard | Live balance, PnL, recent orders |
| Client Info | Full account details — balance, fee tier, trading status |
| Place Order | Form for MARKET / LIMIT / STOP orders |
| History | Full order history, downloadable as JSON or CSV |

---

## Order Types

| Type | Needs | What it does |
|---|---|---|
| MARKET | symbol, side, quantity | Fills immediately at current price |
| LIMIT | symbol, side, quantity, price, time_in_force | Fills once market hits your price |
| STOP | symbol, side, quantity, price, stop_price, time_in_force | Triggers a limit order once the stop price is hit |

---

## Validation

Everything goes through `validation.py` before it's sent to Binance:

- `symbol` — non-empty string (e.g. `BTCUSDT`)
- `side` — `BUY` or `SELL`
- `order_type` — `MARKET`, `LIMIT`, or `STOP`
- `quantity` — number, greater than zero
- `price` — required for LIMIT and STOP
- `stop_price` — required for STOP
- `time_in_force` — required for LIMIT and STOP (`GTC`, `IOC`, `FOK`, `GTX`, `GTD`)
- `price` should NOT be set for MARKET orders

If anything fails validation, you'll see the error right away and nothing gets sent to Binance.

---

## A Few Notes

- STOP orders go through Binance's Algo Order API (`/fapi/v1/algoOrder`), which is what Binance has required since December 2025.
- Requests retry automatically (5 attempts, 3s apart) on `-1007` timeout errors — these happen more than you'd expect on the Testnet.
- `recvWindow` is set to 60,000ms (Binance's max) to give the flaky Testnet some breathing room.
- Order history is pulled live from Binance each time — there's no local database backing it.