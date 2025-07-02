# hft_backtester/src/utils.py

import pandas as pd
from datetime import datetime, timedelta

def format_currency(value: float, currency_symbol: str = "$", decimals: int = 2) -> str:
    """
    Formats a numeric value as a currency string.

    Args:
        value (float): The numeric value to format.
        currency_symbol (str): The symbol for the currency (e.g., '$', '€', '₹').
        decimals (int): The number of decimal places to show.

    Returns:
        str: The formatted currency string.
    """
    if pd.isna(value):
        return f"{currency_symbol} N/A"
    return f"{currency_symbol} {value:,.{decimals}f}"

def get_default_date_range(years_back: int = 5) -> tuple[datetime, datetime]:
    """
    Generates a default start and end date for historical data fetching.

    Args:
        years_back (int): The number of years back from today for the start date.

    Returns:
        tuple[datetime, datetime]: A tuple containing (start_date, end_date) as datetime objects.
    """
    end_date = datetime.now() # Current date and time
    start_date = end_date - timedelta(days=years_back * 365) # Simple calculation for years back
    
    # Return dates at the start/end of the day for consistency
    return start_date.replace(hour=0, minute=0, second=0, microsecond=0), \
           end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

def get_currency_symbol(ticker: str) -> str:
    """
    Determines a currency symbol based on the ticker.
    (This is a simplified example; a real-world app would use an exchange/country mapping).

    Args:
        ticker (str): The stock ticker symbol.

    Returns:
        str: The appropriate currency symbol. Defaults to '$'.
    """
    if ticker.upper().endswith(".NS"): # Common suffix for NSE (India)
        return "₹" # Rupee symbol
    # Add more conditions here for other currencies (e.g., '.L' for GBP, '.TO' for CAD)
    # elif ticker.upper().endswith(".L"):
    #     return "£"
    return "$"


# --- Example usage (for testing this module independently) ---
if __name__ == "__main__":
    print("--- Testing utils.py ---")

    # Test format_currency
    print("\nTesting format_currency:")
    print(f"Formatted: {format_currency(12345.678, '$')}")
    print(f"Formatted (INR): {format_currency(987654.321, '₹', 0)}")
    print(f"Formatted (NaN): {format_currency(float('nan'))}")

    # Test get_default_date_range
    print("\nTesting get_default_date_range:")
    start, end = get_default_date_range(years_back=3)
    print(f"3 years back: Start={start.strftime('%Y-%m-%d')}, End={end.strftime('%Y-%m-%d')}")

    start_1, end_1 = get_default_date_range(years_back=1)
    print(f"1 year back: Start={start_1.strftime('%Y-%m-%d')}, End={end_1.strftime('%Y-%m-%d')}")

    # Test get_currency_symbol
    print("\nTesting get_currency_symbol:")
    print(f"AAPL currency: {get_currency_symbol('AAPL')}")
    print(f"RELIANCE.NS currency: {get_currency_symbol('RELIANCE.NS')}")
    print(f"TSLA currency: {get_currency_symbol('TSLA')}")

    print("\n--- utils.py testing complete ---")