# hft_backtester/src/data_handler.py

import yfinance as yf
import pandas as pd
from datetime import datetime

def fetch_historical_data(
    ticker: str,
    start_date: str, # Format: 'YYYY-MM-DD'
    end_date: str,   # Format: 'YYYY-MM-DD'
    interval: str = "1d" # '1d' for daily, '1h' for hourly etc. (yfinance specific)
) -> pd.DataFrame:
    """
    Fetches historical market data for a given ticker, date range, and interval.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL', 'RELIANCE.NS').
                      For Indian stocks, ensure correct suffix (e.g., '.NS' for NSE).
        start_date (str): Start date in 'YYYY-MM-DD' string format.
        end_date (str): End date in 'YYYY-MM-DD' string format.
        interval (str): Data interval. Common intervals:
                        '1d' (daily), '1wk' (weekly), '1mo' (monthly).
                        Intraday intervals: '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h'.
                        Note: yfinance has limitations on intraday data depth and history.

    Returns:
        pd.DataFrame: A DataFrame with historical OHLCV (Open, High, Low, Close, Volume)
                      data, indexed by date. Returns an empty DataFrame if data fetching fails.
                      The 'Close' column is ensured to be numeric.
    """
    try:
        # Use yf.download to get the data
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

        if data.empty:
            print(f"Warning: No data fetched for {ticker} from {start_date} to {end_date} at {interval} interval.")
            return pd.DataFrame() # Return empty DataFrame on no data

        # Ensure the index is a DatetimeIndex and sort it chronologically
        # This is crucial for time-series operations
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()

        # Check for and ensure 'Close' column exists and is numeric
        if 'Close' not in data.columns:
            # yfinance usually provides 'Close', but defensive check is good
            raise ValueError(f"'Close' column not found in fetched data for {ticker}.")
        
        # Convert 'Close' to numeric, coercing errors to NaN and then dropping rows with NaNs
        # This handles cases where data might contain non-numeric values
        data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
        data.dropna(subset=['Close'], inplace=True) # Drop rows where 'Close' couldn't be converted

        if data.empty:
            print(f"Warning: No valid 'Close' price data after cleaning for {ticker}.")
            return pd.DataFrame()

        # Return relevant columns. We'll mainly use 'Close' for SMA, but OHLCV is often useful.
        return data[['Open', 'High', 'Low', 'Close', 'Volume']]

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame() # Return empty DataFrame on error


# --- Example usage (for testing this module independently) ---
# This block runs only when data_handler.py is executed directly (e.g., python src/data_handler.py)
# It's good practice for module-level testing.
if __name__ == "__main__":
    print("--- Testing data_handler.py ---")

    # Test case 1: Valid daily data for a major US stock
    test_ticker_us = "MSFT"
    test_start_us = "2023-01-01"
    test_end_us = "2024-01-01"
    print(f"\nFetching daily data for {test_ticker_us}...")
    df_us = fetch_historical_data(test_ticker_us, test_start_us, test_end_us, "1d")
    if not df_us.empty:
        print("Success!")
        print(df_us.head())
        print(f"Data shape: {df_us.shape}")
    else:
        print(f"Failed to fetch data for {test_ticker_us}.")

    # Test case 2: Valid daily data for an Indian stock (NSE)
    # Ensure you use the correct suffix for Indian stocks, typically '.NS' for NSE
    test_ticker_in = "RELIANCE.NS"
    test_start_in = "2023-01-01"
    test_end_in = "2024-01-01"
    print(f"\nFetching daily data for {test_ticker_in}...")
    df_in = fetch_historical_data(test_ticker_in, test_start_in, test_end_in, "1d")
    if not df_in.empty:
        print("Success!")
        print(df_in.head())
        print(f"Data shape: {df_in.shape}")
    else:
        print(f"Failed to fetch data for {test_ticker_in}.")

    # Test case 3: Invalid ticker
    print("\nFetching data for an invalid ticker (INVALIDSTOCK)...")
    df_invalid = fetch_historical_data("INVALIDSTOCK", "2023-01-01", "2024-01-01")
    if df_invalid.empty:
        print("Successfully handled invalid ticker.")
    else:
        print("Error: Fetched data for an invalid ticker.")

    # Test case 4: Intraday data (last 7 days, 1-hour interval)
    # Note: yfinance has severe limitations on historical intraday data.
    # It might only return a few days or weeks depending on the interval.
    # For robust HFT, you'd use a dedicated low-latency market data provider.
    now = datetime.now()
    intraday_start = (now - pd.Timedelta(days=7)).strftime('%Y-%m-%d')
    intraday_end = now.strftime('%Y-%m-%d') # Use current date for end
    print(f"\nFetching 1-hour data for {test_ticker_us} from {intraday_start} to {intraday_end}...")
    df_intraday = fetch_historical_data(test_ticker_us, intraday_start, intraday_end, "1h")
    if not df_intraday.empty:
        print("Success (intraday)!")
        print(df_intraday.head())
        print(f"Data shape: {df_intraday.shape}")
    else:
        print(f"Failed to fetch intraday data for {test_ticker_us} or no data in range.")

    print("\n--- data_handler.py testing complete ---")