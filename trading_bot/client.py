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

load_dotenv()  # Load variables from .env into os.environ

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


def signed_request(method: str, path: str, params: dict = None) -> dict:
    """
    Call a SIGNED endpoint (e.g. /fapi/v2/account, /fapi/v1/order).
    Adds timestamp + recvWindow automatically.
    """
    params = params.copy() if params else {}
    params["timestamp"] = int(time.time() * 1000)
    params.setdefault("recvWindow", 5000)

    query_string = _sign(params)
    url = f"{BASE_URL}{path}?{query_string}"

    resp = session.request(method, url)
    resp.raise_for_status()
    return resp.json()


def public_request(method: str, path: str, params: dict = None) -> dict:
    """Call a public (unsigned) endpoint, e.g. /fapi/v1/ping, /fapi/v1/ticker/price."""
    url = f"{BASE_URL}{path}"
    resp = session.request(method, url, params=params or {})
    resp.raise_for_status()
    return resp.json()


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