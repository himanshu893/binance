"""
Flask API server — bridges the frontend to the Binance Futures Testnet.

Endpoints:
  GET  /api/account              -> account balance & info
  GET  /api/orders?symbol=XXXX   -> order history for a symbol
  POST /api/orders               -> place a new order
"""

import sys
import os

# Make sure trading_bot modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify
from flask_cors import CORS

from client import signed_request, public_request
from orders import submit_order
from validation import OrderValidationError

app = Flask(__name__)
CORS(app)  # Allow frontend to talk to this server


# ──────────────────────────────────────────────
# GET /api/account
# ──────────────────────────────────────────────
@app.route("/api/account")
def get_account():
    try:
        data = signed_request("GET", "/fapi/v2/account")
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# GET /api/orders?symbol=BTCUSDT&limit=20
# ──────────────────────────────────────────────
@app.route("/api/orders", methods=["GET"])
def get_orders():
    symbol = request.args.get("symbol", "BTCUSDT").upper()
    limit  = int(request.args.get("limit", 20))
    try:
        data = signed_request("GET", "/fapi/v1/allOrders", {
            "symbol": symbol,
            "limit":  limit
        })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# POST /api/orders
# Body: { symbol, side, order_type, quantity,
#         price?, time_in_force?, stop_price? }
# ──────────────────────────────────────────────
@app.route("/api/orders", methods=["POST"])
def place_order():
    body = request.get_json(force=True) or {}
    try:
        result = submit_order(
            symbol        = body.get("symbol"),
            side          = body.get("side"),
            order_type    = body.get("order_type"),
            quantity      = body.get("quantity"),
            price         = body.get("price"),
            time_in_force = body.get("time_in_force"),
            stop_price    = body.get("stop_price"),
        )
        return jsonify(result)
    except OrderValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Starting Binance Bot API server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
