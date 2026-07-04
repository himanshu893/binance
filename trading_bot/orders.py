"""
Entry point for placing orders on Binance Futures Testnet.
Flow: raw input -> validate_order() -> signed_request()
"""

from validation import validate_order, OrderValidationError
from client import signed_request


def submit_order(symbol, side, order_type, quantity, price=None, time_in_force=None):
    """
    Validate raw input, then place the order if valid.
    Returns the Binance API response dict, or raises OrderValidationError
    before any request is sent if input is invalid.
    """
    clean = validate_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        time_in_force=time_in_force,
    )

    params = {
        "symbol": clean["symbol"],
        "side": clean["side"],
        "type": clean["type"],
        "quantity": clean["quantity"]
    }
    if "price" in clean:
        params["price"] = clean["price"]
    if "timeInForce" in clean:
        params["timeInForce"] = clean["timeInForce"]

    return signed_request("POST", "/fapi/v1/order", params)


def print_order_summary(request: dict, response: dict = None, error: str = None) -> None:
    """
    Print a human-readable summary of an order attempt.
    request: the raw params passed to submit_order (symbol, side, order_type, quantity, price...)
    response: the Binance API response dict (on success)
    error: error message string (on failure) — pass this instead of response
    """
    print("=" * 40)
    print("ORDER REQUEST")
    print("-" * 40)
    for k, v in request.items():
        if v is not None:
            print(f"{k:15}: {v}")

    print("-" * 40)
    if error:
        print("STATUS          : FAILED")
        print(f"REASON          : {error}")
    else:
        print("ORDER RESPONSE")
        print(f"{'orderId':15}: {response.get('orderId')}")
        print(f"{'status':15}: {response.get('status')}")
        print(f"{'executedQty':15}: {response.get('executedQty')}")
        avg_price = response.get('avgPrice')
        if avg_price is not None:
            print(f"{'avgPrice':15}: {avg_price}")
        print("-" * 40)
        print("STATUS          : SUCCESS")
    print("=" * 40)


if __name__ == "__main__":
    print("--- Binance Futures Order Entry ---")
    symbol = input("Enter symbol (e.g. BTCUSDT): ").strip()
    side = input("Enter side (BUY or SELL): ").strip()
    order_type = input("Enter order type (MARKET or LIMIT): ").strip()
    quantity = input("Enter quantity (e.g. 0.001): ").strip()
    
    price = None
    time_in_force = None
    
    if order_type.strip().upper() == "LIMIT":
        price = input("Enter price: ").strip()
        time_in_force = input("Enter time_in_force (e.g. GTC): ").strip()
        
    request = dict(
        symbol=symbol, 
        side=side, 
        order_type=order_type, 
        quantity=quantity,
        price=price,
        time_in_force=time_in_force
    )

    try:
        result = submit_order(**request)
        print_order_summary(request, response=result)
    except OrderValidationError as e:
        print_order_summary(request, error=str(e))
    except Exception as e:
        print_order_summary(request, error=f"API Error or other exception: {str(e)}")