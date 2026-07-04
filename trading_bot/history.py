"""
Fetch actual order history from Binance Futures Testnet API.
"""
from client import signed_request
from datetime import datetime

def fetch_and_print_orders(symbol: str, limit: int = 10):
    print(f"\nFetching recent orders for {symbol} from Binance API...")
    params = {
        "symbol": symbol.strip().upper(),
        "limit": limit
    }
    
    try:
        # Request order history for the symbol
        orders = signed_request("GET", "/fapi/v1/allOrders", params)
        
        if not orders:
            print("No orders found for this symbol.")
            return

        print("\n" + "=" * 80)
        print(f"{'TIME (Local)':<20} | {'SIDE':<5} | {'TYPE':<7} | {'QTY':<8} | {'PRICE':<8} | {'STATUS':<10} | {'ORDER ID'}")
        print("-" * 80)
        
        for o in orders:
            # Binance timestamps are in milliseconds
            dt = datetime.fromtimestamp(o['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            side = o.get('side', '')
            otype = o.get('type', '')
            qty = o.get('origQty', '')
            price = o.get('price', '0')
            if price == "0" or price == "0.0":
                price = "MKT"
            status = o.get('status', '')
            oid = o.get('orderId', '')
            
            print(f"{dt:<20} | {side:<5} | {otype:<7} | {qty:<8} | {price:<8} | {status:<10} | {oid}")
            
        print("=" * 80)
        
    except Exception as e:
        print(f"\nFailed to fetch orders: {e}")

if __name__ == "__main__":
    print("--- Binance API Order History ---")
    sym = input("Enter symbol to check (e.g. BTCUSDT): ").strip()
    if sym:
        fetch_and_print_orders(sym)
    else:
        print("Symbol is required.")
