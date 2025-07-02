# hft_backtester/src/strategy.py

import pandas as pd
import numpy as np

def calculate_smas(df: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    """
    Calculates Simple Moving Averages (SMAs) for the 'Close' price.

    Args:
        df (pd.DataFrame): Input DataFrame containing a 'Close' price column.
                           Must have a DatetimeIndex and be sorted chronologically.
        short_window (int): The number of periods for the shorter SMA.
        long_window (int): The number of periods for the longer SMA.

    Returns:
        pd.DataFrame: A copy of the input DataFrame with 'SMA_Short' and 'SMA_Long'
                      columns added. Initial NaN values will be present where there
                      aren't enough periods for the rolling calculation.

    Raises:
        ValueError: If 'Close' column is missing or if window sizes are invalid.
        TypeError: If 'Close' column is not numeric.
    """
    if 'Close' not in df.columns:
        raise ValueError("DataFrame must contain a 'Close' column to calculate SMAs.")
    if not pd.api.types.is_numeric_dtype(df['Close']):
        raise TypeError("The 'Close' price column must be numeric.")
    if short_window <= 0 or long_window <= 0:
        raise ValueError("SMA window periods must be positive integers.")
    if short_window >= long_window:
        raise ValueError("Short SMA window must be strictly less than Long SMA window.")

    # Always work on a copy to avoid modifying the original DataFrame passed in,
    # preventing "SettingWithCopyWarning" and unexpected side effects.
    df_copy = df.copy() 
    
    # Calculate SMAs using vectorized Pandas rolling window function
    # min_periods=1 allows calculation even if fewer than 'window' periods are available at the start
    df_copy['SMA_Short'] = df_copy['Close'].rolling(window=short_window, min_periods=1).mean()
    df_copy['SMA_Long'] = df_copy['Close'].rolling(window=long_window, min_periods=1).mean()
    
    return df_copy

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates buy and sell signals based on SMA crossover.

    Signals are generated as follows:
    - Buy (1.0): When 'SMA_Short' crosses above 'SMA_Long'.
    - Sell (-1.0): When 'SMA_Short' crosses below 'SMA_Long'.
    - Hold (0.0): Otherwise.

    Args:
        df (pd.DataFrame): DataFrame containing 'SMA_Short' and 'SMA_Long' columns.
                           It should also have a DatetimeIndex and be sorted.
                           Assumes that NaNs from SMA calculation have been handled
                           (e.g., dropped) before passing to this function,
                           as signals cannot be generated on NaN values.

    Returns:
        pd.DataFrame: A copy of the input DataFrame with 'Signal' and 'Position' columns added.
                      'Signal' indicates the raw buy/sell point.
                      'Position' represents the actual holding: 1 for long, -1 for short, 0 for cash.
                      'Position' is lagged to prevent look-ahead bias (trades happen at the *next* period's open).

    Raises:
        ValueError: If 'SMA_Short' or 'SMA_Long' columns are missing.
    """
    if 'SMA_Short' not in df.columns or 'SMA_Long' not in df.columns:
        raise ValueError("DataFrame must contain 'SMA_Short' and 'SMA_Long' columns.")
    
    df_copy = df.copy()

    # Create a boolean series indicating when short SMA is greater than long SMA
    # This is our raw "crossover state"
    df_copy['SMA_Crossover_State'] = df_copy['SMA_Short'] > df_copy['SMA_Long']

    # Generate raw signals based on state changes:
    # A 'buy' signal (1.0) occurs when the crossover state changes from False to True.
    # A 'sell' signal (-1.0) occurs when the crossover state changes from True to False.
    # We use .astype(int) to convert boolean to 0/1 for diff calculation.
    df_copy['Signal'] = df_copy['SMA_Crossover_State'].astype(int).diff()

    # Clean up signals:
    # If Signal is 1, it's a buy.
    # If Signal is -1, it's a sell.
    # Any other value (0 or NaN) means no action or initial state.
    df_copy['Signal'] = df_copy['Signal'].replace(0, np.nan).fillna(0) # Keep only actual crossovers
    
    # Ensure -1 for sell and 1 for buy. Raw diff might be -1 or 1, but we need
    # to make sure it's consistent if we had initial state changes.
    df_copy.loc[df_copy['Signal'] > 0, 'Signal'] = 1.0   # Buy
    df_copy.loc[df_copy['Signal'] < 0, 'Signal'] = -1.0 # Sell

    # Calculate 'Position': This represents the actual holding in the market.
    # cumsum() applies the buy/sell signals to create a continuous position.
    # For example: 0 -> 1 (buy), 1 -> 0 (sell), 0 -> -1 (short sell), -1 -> 0 (cover short)
    # This needs careful consideration. For a simple long-only strategy:
    # Position = 1.0 if 'Signal' indicates buy, 0.0 if 'Signal' indicates sell or hold.
    # For a long/short strategy (as implied by -1 signal):
    # Position = df_copy['Signal'].replace(0, pd.NA).ffill().fillna(0) # Forward fill last known signal
    # Or more robustly, track the current position based on signals
    
    # For a long-only strategy (simplest):
    # If buy signal (1.0), set position to 1.0 (long). If sell signal (-1.0), set position to 0.0 (cash).
    # Otherwise, maintain previous position.
    df_copy['Position'] = np.nan # Initialize with NaN
    
    # Set initial position based on first signal (if any)
    first_signal_idx = df_copy['Signal'].ne(0).idxmax() if df_copy['Signal'].ne(0).any() else None
    if first_signal_idx:
        df_copy.loc[first_signal_idx, 'Position'] = df_copy.loc[first_signal_idx, 'Signal'] if df_copy.loc[first_signal_idx, 'Signal'] == 1.0 else 0.0
    else: # No signals generated
        df_copy['Position'] = 0.0

    # Fill forward positions and then set subsequent sell signals to 0.
    # This logic assumes we want to go long (1) or be flat (0).
    # If df_copy['Signal'] is 1, we enter a long position (1).
    # If df_copy['Signal'] is -1, we exit any long position (0).
    # Otherwise, we hold the current position.
    
    # A more general approach for position management using cumsum on adjusted signals:
    # First, let's create a 'long_entry_exit' column: 1 for buy, -1 for sell, 0 otherwise
    df_copy['Action'] = 0
    df_copy.loc[df_copy['Signal'] == 1.0, 'Action'] = 1 # Buy (Go Long)
    df_copy.loc[df_copy['Signal'] == -1.0, 'Action'] = -1 # Sell (Go Flat / Cover Short)

    # Now, convert Actions to positions. This assumes we only take 1 unit position.
    # If we are long (position 1) and get a sell signal (-1), new position is 0.
    # If we are flat (position 0) and get a buy signal (1), new position is 1.
    # This is a stateless position calculation, suitable for simple buy/sell points.
    
    # For the SMA Crossover, let's assume a simple state machine:
    # Start at 0 (cash). When SMA_Short > SMA_Long, go to 1 (long). When SMA_Short < SMA_Long, go to 0 (cash).
    
    df_copy['Position'] = np.where(df_copy['SMA_Short'] > df_copy['SMA_Long'], 1.0, 0.0)
    
    # Important for backtesting: To avoid look-ahead bias, trade execution happens *after* the signal is generated.
    # If a signal is generated on day T, the trade occurs at the opening of day T+1.
    # We shift the 'Position' column by one period. The last row will be NaN, which we fill with 0.
    df_copy['Position'] = df_copy['Position'].shift(1).fillna(0.0)

    # If the first actual data point has SMA_Short > SMA_Long, the initial position
    # should be 0 because we haven't received a signal to enter yet.
    # The .shift(1) correctly handles this by making the first 'Position' NaN, which we fill to 0.
    
    return df_copy[['Close', 'SMA_Short', 'SMA_Long', 'Signal', 'Position']]


# --- Example usage (for testing this module independently) ---
if __name__ == "__main__":
    print("--- Testing strategy.py ---")
    
    # Create dummy data for testing
    data = {
        'Close': [100, 102, 105, 103, 107, 110, 108, 112, 115, 113, 117, 120, 118, 122, 125, 123, 128, 130, 127, 132],
        'Volume': [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1500, 1450, 1600, 1550, 1700, 1650, 1800, 1750, 1900, 1850, 2000]
    }
    dates = pd.to_datetime(pd.date_range(start='2024-01-01', periods=len(data['Close'])))
    test_df = pd.DataFrame(data, index=dates)

    print("\nOriginal DataFrame (first 5 rows):")
    print(test_df.head())

    # Test SMA calculation
    short_w = 3
    long_w = 7
    print(f"\nCalculating SMAs (Short: {short_w}, Long: {long_w})...")
    df_with_smas = calculate_smas(test_df, short_w, long_w)
    print(df_with_smas.tail()) # Show last few rows with SMAs

    # Test signal generation (dropna() is important here, as generate_signals expects no NaNs)
    print("\nGenerating signals...")
    df_with_signals = generate_signals(df_with_smas.dropna()) # Pass a clean DataFrame
    print(df_with_signals.tail(10)) # Show relevant part with signals and positions

    # Verify a crossover manually (e.g., in df_with_signals.tail(10))
    # Look for a row where Signal is 1 or -1 and check if SMA_Short crossed SMA_Long.
    # Then check if Position is correctly lagged.

    print("\n--- strategy.py testing complete ---")