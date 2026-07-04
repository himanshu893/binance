"""
Input validation for Binance Futures order placement.
Run before signing/sending any request.
"""

ALLOWED_SIDES = ["BUY", "SELL"]
ALLOWED_TYPES = ["MARKET", "LIMIT", "STOP"]


class OrderValidationError(ValueError):
    pass


def validate_order(symbol: str, side: str, order_type: str, quantity, price=None,
                    time_in_force: str = None, stop_price=None) -> dict:
    """
    Validates and normalizes order params.
    Returns a cleaned dict on success; raises OrderValidationError on failure.
    """
    errors = []

    # --- symbol ---
    if not symbol or not isinstance(symbol, str):
        errors.append("symbol must be a non-empty string")
        symbol_clean = None
    else:
        symbol_clean = symbol.strip().upper()

    # --- side ---
    side_clean = side.strip().upper() if isinstance(side, str) else side
    if side_clean not in ALLOWED_SIDES:
        errors.append(f"side must be one of {ALLOWED_SIDES}, got {side!r}")

    # --- order_type ---
    type_clean = order_type.strip().upper() if isinstance(order_type, str) else order_type
    if type_clean not in ALLOWED_TYPES:
        errors.append(f"order_type must be one of {ALLOWED_TYPES}, got {order_type!r}")

    # --- quantity ---
    qty_clean = None
    try:
        qty_clean = float(quantity)
        if qty_clean <= 0:
            errors.append(f"quantity must be strictly greater than zero, got {quantity!r}")
    except (TypeError, ValueError):
        errors.append(f"quantity must be a number, got {quantity!r}")

    # --- LIMIT and STOP specific rules ---
    price_clean = None
    stop_price_clean = None
    tif_clean = None
    if type_clean in ("LIMIT", "STOP"):
        try:
            price_clean = float(price)
            if price_clean <= 0:
                errors.append(f"price must be strictly greater than zero, got {price!r}")
        except (TypeError, ValueError):
            errors.append(f"price is required for {type_clean} orders and must be a number, got {price!r}")

        if not time_in_force:
            errors.append(f"time_in_force is required for {type_clean} orders (e.g. 'GTC')")
        else:
            tif_clean = time_in_force.strip().upper()
            if tif_clean not in ("GTC", "IOC", "FOK", "GTX", "GTD"):
                errors.append(f"time_in_force must be one of GTC/IOC/FOK/GTX/GTD, got {time_in_force!r}")
                
        if type_clean == "STOP":
            try:
                stop_price_clean = float(stop_price)
                if stop_price_clean <= 0:
                    errors.append(f"stop_price must be strictly greater than zero, got {stop_price!r}")
            except (TypeError, ValueError):
                errors.append(f"stop_price is required for STOP orders and must be a number, got {stop_price!r}")
    elif type_clean == "MARKET":
        if price is not None:
            errors.append("price should not be set for MARKET orders")
        if stop_price is not None:
            errors.append("stop_price should not be set for MARKET orders")

    if errors:
        raise OrderValidationError("; ".join(errors))

    result = {
        "symbol": symbol_clean,
        "side": side_clean,
        "type": type_clean,
        "quantity": qty_clean,
    }
    if type_clean in ("LIMIT", "STOP"):
        result["price"] = price_clean
        result["timeInForce"] = tif_clean
    if type_clean == "STOP":
        result["stopPrice"] = stop_price_clean

    return result


if __name__ == "__main__":
    # quick manual checks
    print(validate_order("btcusdt", "buy", "market", 0.001))
    print(validate_order("ethusdt", "SELL", "LIMIT", "0.5", price="3000", time_in_force="gtc"))

    for bad in [
        dict(symbol="BTCUSDT", side="HOLD", order_type="MARKET", quantity=1),
        dict(symbol="BTCUSDT", side="BUY", order_type="STOP", quantity=1),
        dict(symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0),
        dict(symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=-1),
        dict(symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=1),  # missing price/tif
    ]:
        try:
            validate_order(**bad)
        except OrderValidationError as e:
            print("Rejected:", bad, "->", e)