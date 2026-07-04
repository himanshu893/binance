"""
Minimal Binance USD-M Futures Testnet client.
Handles HMAC-SHA256 request signing for signed endpoints.

Env vars required:
    BINANCE_API_KEY
    BINANCE_API_SECRET
"""

import os
import time
import hmac
import hashlib
import urllib.parse
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://testnet.binancefuture.com"

API_KEY = os.environ["BINANCE_API_KEY"]
API_SECRET = os.environ["BINANCE_API_SECRET"]

session = requests.Session()
session.headers.update({"X-MBX-APIKEY": API_KEY})


def _sign(params: dict) -> str:
    """Return query string with signature appended."""
    query_string = urllib.parse.urlencode(params, doseq=True)
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{query_string}&signature={signature}"


def signed_request(method: str, path: str, params: dict = None,
                   retries: int = 5, retry_delay: float = 3.0) -> dict:
    """
    Call a SIGNED endpoint (e.g. /fapi/v2/account, /fapi/v1/order).
    Adds timestamp + recvWindow automatically.
    Retries up to `retries` times on -1007 Testnet timeout errors.
    """
    last_error = None
    for attempt in range(1, retries + 1):
        p = (params or {}).copy()
        p["timestamp"] = int(time.time() * 1000)   # fresh timestamp each retry
        p.setdefault("recvWindow", 60000)  # max allowed by Binance

        query_string = _sign(p)
        url = f"{BASE_URL}{path}?{query_string}"

        try:
            resp = session.request(method, url, timeout=15)
        except requests.exceptions.Timeout:
            last_error = Exception("Request timed out (no response from Binance).")
            if attempt < retries:
                time.sleep(retry_delay)
            continue

        if resp.ok:
            return resp.json()

        # -1007: Testnet backend timeout — order status unknown, try again
        try:
            body = resp.json()
        except Exception:
            body = {}

        if body.get("code") == -1007 and attempt < retries:
            print(f"[Retry {attempt}/{retries}] -1007 timeout from Binance, retrying in {retry_delay}s…")
            time.sleep(retry_delay)
            last_error = Exception(f"{resp.status_code} {resp.reason}: {resp.text}")
            continue

        raise Exception(f"{resp.status_code} {resp.reason}: {resp.text}")

    raise last_error


def public_request(method: str, path: str, params: dict = None) -> dict:
    """Call a public (unsigned) endpoint, e.g. /fapi/v1/ping, /fapi/v1/ticker/price."""
    url = f"{BASE_URL}{path}"
    resp = session.request(method, url, params=params or {})
    resp.raise_for_status()
    return resp.json()


def place_order(symbol: str, side: str, order_type: str, quantity: str, price: str = None,
                 time_in_force: str = "GTC", reduce_only: bool = False,
                 position_side: str = "BOTH") -> dict:
    """
    Place an order on Futures Testnet.
    side: 'BUY' or 'SELL'
    order_type: 'MARKET' or 'LIMIT'
    quantity/price: pass as strings to avoid float precision issues,
                    respecting the symbol's LOT_SIZE / PRICE_FILTER step size.
    """
    params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
        "positionSide": position_side,
    }
    if order_type == "LIMIT":
        params["timeInForce"] = time_in_force
        params["price"] = price
    if reduce_only:
        params["reduceOnly"] = "true"

    return signed_request("POST", "/fapi/v1/order", params)


if __name__ == "__main__":
    # Sanity checks
    print("Ping:", public_request("GET", "/fapi/v1/ping"))
    print("Server time:", public_request("GET", "/fapi/v1/time"))

    # Signed call — account info
    account = signed_request("GET", "/fapi/v2/account")
    print("Total wallet balance (USDT):", account.get("totalWalletBalance"))

    # Example: place a small market order (BUY 0.001 BTC) — comment out if not needed
    # order = signed_request("POST", "/fapi/v1/order", {
    #     "symbol": "BTCUSDT",
    #     "side": "BUY",
    #     "type": "MARKET",
    #     "quantity": 0.001,
    # })
    # print("Order response:", order)