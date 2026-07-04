

from client import signed_request
from orders import submit_order, print_order_summary
from history import fetch_and_print_orders
from validation import OrderValidationError


def show_account_details():
    account = signed_request("GET", "/fapi/v2/account")
    print("-" * 40)
    print(f"Total wallet balance (USDT): {account.get('totalWalletBalance')}")
    print(f"Available balance (USDT)   : {account.get('availableBalance')}")
    print(f"Unrealized PnL             : {account.get('totalUnrealizedProfit')}")
    print("-" * 40)


def place_order_flow():
    symbol = input("Symbol (e.g. BTCUSDT): ").strip()
    side = input("Side (BUY/SELL): ").strip()
    order_type = input("Order type (MARKET/LIMIT/STOP): ").strip()
    quantity = input("Quantity: ").strip()

    price = None
    time_in_force = None
    stop_price = None
    
    ot_upper = order_type.strip().upper()
    if ot_upper in ("LIMIT", "STOP"):
        price = input("Price: ").strip()
        time_in_force = input("Time in force (GTC/IOC/FOK) [GTC]: ").strip() or "GTC"
    if ot_upper == "STOP":
        stop_price = input("Stop price (trigger): ").strip()

    request = dict(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        time_in_force=time_in_force,
        stop_price=stop_price,
    )

    try:
        result = submit_order(**request)
        print_order_summary(request, response=result)
    except OrderValidationError as e:
        print_order_summary(request, error=str(e))
    except Exception as e:
        print_order_summary(request, error=str(e))


def show_api_history():
    sym = input("Symbol to check (e.g. BTCUSDT): ").strip()
    if sym:
        fetch_and_print_orders(sym)
    else:
        print("Symbol is required.")


def main():
    menu = (
        "\n=== Binance Futures Testnet CLI ===\n"
        "1. Account details\n"
        "2. Place order\n"
        "3. Live API order history\n"
        "4. Exit\n"
    )

    while True:
        print(menu)
        choice = input("Select an option: ").strip()

        if choice == "1":
            show_account_details()
        elif choice == "2":
            place_order_flow()
        elif choice == "3":
            show_api_history()
        elif choice == "4":
            print("Exiting.")
            break
        else:
            print("Invalid option, choose 1-4.")


if __name__ == "__main__":
    main()