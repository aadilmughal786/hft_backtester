# hft_backtester/src/data_handler.py

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

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
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

        # --- NEW FIX: Handle MultiIndex columns from yfinance ---
        # yfinance can sometimes return MultiIndex columns, especially with auto_adjust=True
        # or when fetching multiple tickers. We need to flatten them.
        if isinstance(data.columns, pd.MultiIndex):
            # Option 1: Take the second level (e.g., 'Close', 'High') - simpler
            data.columns = data.columns.droplevel(1)
            # Or Option 2: Join levels (e.g., 'Close_MSFT') - more explicit
            # data.columns = ['_'.join(col).strip() for col in data.columns.values]
            
            # After droplevel, ensure unique columns if multiple tickers were fetched
            # (though for single ticker, this isn't strictly necessary but robust)
            data = data.loc[:,~data.columns.duplicated()] # Keep first occurrence of duplicate columns
        # --- END NEW FIX ---

        if data.empty:
            print(f"Warning: No data fetched for {ticker} from {start_date} to {end_date} at {interval} interval.")
            return pd.DataFrame()

        # Ensure the index is a DatetimeIndex and sort it chronologically
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()

        # Check for and ensure 'Close' column exists and is numeric
        if 'Close' not in data.columns:
            raise ValueError(f"'Close' column not found in fetched data for {ticker}. Available columns: {data.columns.tolist()}")
        
        # Convert 'Close' to numeric, coercing errors to NaN and then dropping rows with NaNs
        data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
        data.dropna(subset=['Close'], inplace=True) # Drop rows where 'Close' couldn't be converted

        if data.empty:
            print(f"Warning: No valid 'Close' price data after cleaning for {ticker}.")
            return pd.DataFrame()

        return data[['Open', 'High', 'Low', 'Close', 'Volume']]

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()


# --- Example usage (for testing this module independently) ---
if __name__ == "__main__":
    print("--- Testing data_handler.py ---")

    # Set end date to yesterday to avoid issues with current-day incomplete data
    yesterday = datetime.now() - timedelta(days=1)
    test_end_date_str = yesterday.strftime('%Y-%m-%d')

    # Test case 1: Valid daily data for a major US stock (MSFT)
    test_ticker_us = "MSFT"
    test_start_us = "2023-01-01"
    
    print(f"\nFetching daily data for {test_ticker_us}...")
    df_us = fetch_historical_data(test_ticker_us, test_start_us, test_end_date_str, "1d")
    if not df_us.empty:
        print(f"\n--- Daily Data for {test_ticker_us} (Success) ---")
        print(df_us.head())
        print(df_us.tail())
        print(f"Data shape: {df_us.shape}")
        print(f"Final columns: {df_us.columns.tolist()}") # Confirm flattened columns
    else:
        print(f"\nFailed to fetch data for {test_ticker_us}.")

    # Test case 2: Valid daily data for an Indian stock (NSE)
    test_ticker_in = "RELIANCE.NS"
    test_start_in = "2023-01-01"
    
    print(f"\nFetching daily data for {test_ticker_in}...")
    df_in = fetch_historical_data(test_ticker_in, test_start_in, test_end_date_str, "1d")
    if not df_in.empty:
        print(f"\n--- Daily Data for {test_ticker_in} (Success) ---")
        print(df_in.head())
        print(df_in.tail())
        print(f"Data shape: {df_in.shape}")
        print(f"Final columns: {df_in.columns.tolist()}") # Confirm flattened columns
    else:
        print(f"\nFailed to fetch data for {test_ticker_in}.")

    # Test case 3: Invalid ticker
    print("\nFetching data for an invalid ticker (INVALIDSTOCKTEST)...")
    df_invalid = fetch_historical_data("INVALIDSTOCKTEST", "2023-01-01", "2024-01-01")
    if df_invalid.empty:
        print("Successfully handled invalid ticker.")
    else:
        print("Error: Fetched data for an invalid ticker. (This should not happen).")

    print("\n--- data_handler.py testing complete ---")