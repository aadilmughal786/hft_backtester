# hft_backtester/src/backtester.py

import pandas as pd
import numpy as np

def run_backtest(df: pd.DataFrame, initial_capital: float = 100000.0) -> pd.DataFrame:
    """
    Runs a backtest of the trading strategy on historical data.

    Assumes the input DataFrame `df` already contains:
    - 'Close': The closing price of the asset.
    - 'Position': The calculated position (1.0 for long, 0.0 for cash) for each day,
                  shifted to avoid look-ahead bias (i.e., position for day T is based
                  on signal from day T-1).

    Args:
        df (pd.DataFrame): DataFrame with historical data, including 'Close' and 'Position'.
                           Must have a DatetimeIndex.
        initial_capital (float): The starting capital for the backtest.

    Returns:
        pd.DataFrame: A DataFrame representing the portfolio's performance over time,
                      including 'Holdings', 'Cash', 'Total' value, 'Daily_Return',
                      'Cumulative_Return', 'Daily_Asset_Return', and 'Cumulative_Asset_Return'.
                      Returns an empty DataFrame if input is invalid.

    Raises:
        ValueError: If required columns ('Close', 'Position') are missing or if
                    initial capital is not positive.
        TypeError: If 'Close' or 'Position' columns are not numeric.
    """
    if df.empty:
        print("Error: Input DataFrame for backtest is empty.")
        return pd.DataFrame()
    if 'Close' not in df.columns or 'Position' not in df.columns:
        raise ValueError("DataFrame must contain 'Close' and 'Position' columns for backtesting.")
    if not pd.api.types.is_numeric_dtype(df['Close']) or not pd.api.types.is_numeric_dtype(df['Position']):
        raise TypeError("Columns 'Close' and 'Position' must be numeric.")
    if initial_capital <= 0:
        raise ValueError("Initial capital must be a positive value.")

    # Work on a copy to avoid modifying the original DataFrame
    df_backtest = df.copy()

    # Calculate daily returns of the asset
    df_backtest['Daily_Asset_Return'] = df_backtest['Close'].pct_change()
    # Fix: Reassign instead of inplace=True
    df_backtest['Daily_Asset_Return'] = df_backtest['Daily_Asset_Return'].fillna(0) # First day's return is 0

    # Calculate strategy returns: Position for day T * Asset_Return for day T
    df_backtest['Strategy_Daily_Return'] = df_backtest['Position'] * df_backtest['Daily_Asset_Return']

    # Initialize cash with initial_capital and holdings with 0 for the first day
    cash = [initial_capital]
    holdings = [0.0]
    
    # Iterate through the DataFrame to simulate cash and holdings for each day
    for i in range(1, len(df_backtest)):
        prev_cash = cash[-1]
        prev_holdings_value = holdings[-1]
        
        current_position = df_backtest['Position'].iloc[i]
        prev_position = df_backtest['Position'].iloc[i-1]
        
        current_close = df_backtest['Close'].iloc[i]
        prev_close = df_backtest['Close'].iloc[i-1]

        # Handle division by zero for percentage change if prev_close was 0 (shouldn't happen for stock prices)
        if prev_close == 0:
            asset_change_factor = 1.0 # No change if prev_close was 0
        else:
            asset_change_factor = current_close / prev_close

        if current_position == 1.0 and prev_position == 0.0: # BUY signal (entering long)
            shares_bought = prev_cash / current_close
            holdings.append(shares_bought * current_close) # Value of holdings
            cash.append(0.0) # All cash invested
        elif current_position == 0.0 and prev_position == 1.0: # SELL signal (exiting long)
            realized_cash = prev_holdings_value * asset_change_factor
            cash.append(realized_cash)
            holdings.append(0.0)
        elif current_position == 1.0 and prev_position == 1.0: # STAY LONG
            holdings.append(prev_holdings_value * asset_change_factor)
            cash.append(prev_cash)
        else: # STAY CASH (current_position == 0.0 and prev_position == 0.0)
            cash.append(prev_cash)
            holdings.append(0.0)

    # Assign the calculated cash and holdings to the DataFrame
    df_backtest['Cash'] = cash
    df_backtest['Holdings'] = holdings
    
    # Calculate Total_Portfolio_Value based on explicit Cash + Holdings
    df_backtest['Total_Portfolio_Value'] = df_backtest['Cash'] + df_backtest['Holdings']
    
    # Calculate daily and cumulative returns for the portfolio
    df_backtest['Daily_Return'] = df_backtest['Total_Portfolio_Value'].pct_change()
    # Fix: Reassign instead of inplace=True
    df_backtest['Daily_Return'] = df_backtest['Daily_Return'].fillna(0) # First day's return is 0

    df_backtest['Cumulative_Return'] = (1 + df_backtest['Daily_Return']).cumprod() - 1 # Adjusted to start from 0
    # Ensure the first cumulative return is 0.0
    if not df_backtest.empty:
        df_backtest.loc[df_backtest.index[0], 'Cumulative_Return'] = 0.0

    # Calculate Cumulative Asset Return for benchmark
    df_backtest['Cumulative_Asset_Return'] = (1 + df_backtest['Daily_Asset_Return']).cumprod() - 1
    if not df_backtest.empty:
        df_backtest.loc[df_backtest.index[0], 'Cumulative_Asset_Return'] = 0.0

    return df_backtest[[
        'Close', 'Position', 'Total_Portfolio_Value', 'Daily_Return', 'Cumulative_Return',
        'Cash', 'Holdings', 'Daily_Asset_Return', 'Cumulative_Asset_Return'
    ]]

def calculate_performance_metrics(portfolio_df: pd.DataFrame) -> dict:
    """
    Calculates key performance metrics for the backtested strategy.

    Args:
        portfolio_df (pd.DataFrame): DataFrame returned by run_backtest.
                                     Must contain 'Daily_Return', 'Daily_Asset_Return',
                                     'Total_Portfolio_Value', and 'Cumulative_Return' columns.

    Returns:
        dict: A dictionary of performance metrics. Returns an error dict if input is invalid.
    """
    required_cols = ['Daily_Return', 'Daily_Asset_Return', 'Total_Portfolio_Value', 'Cumulative_Return']
    if portfolio_df.empty or not all(col in portfolio_df.columns for col in required_cols):
        return {"Error": "Invalid portfolio DataFrame for performance calculation. Missing required columns."}

    # Drop the first NaN from daily returns if present (due to pct_change).
    # These should already be handled by fillna(0) in run_backtest, but
    # .dropna() here makes the std() calculation robust.
    strategy_returns = portfolio_df['Daily_Return'].dropna()
    asset_returns = portfolio_df['Daily_Asset_Return'].dropna()

    annualization_factor = 252 # Assuming daily data, 252 trading days in a year

    cumulative_strategy_return = portfolio_df['Cumulative_Return'].iloc[-1]
    cumulative_asset_return = portfolio_df['Cumulative_Asset_Return'].iloc[-1]

    num_trading_days = len(strategy_returns)
    
    if num_trading_days > 0:
        annualized_strategy_return = (1 + cumulative_strategy_return)**(annualization_factor / num_trading_days) - 1
        annualized_asset_return = (1 + cumulative_asset_return)**(annualization_factor / num_trading_days) - 1
    else:
        annualized_strategy_return = 0.0
        annualized_asset_return = 0.0

    annualized_strategy_volatility = strategy_returns.std() * np.sqrt(annualization_factor) if len(strategy_returns) > 1 else 0.0
    annualized_asset_volatility = asset_returns.std() * np.sqrt(annualization_factor) if len(asset_returns) > 1 else 0.0

    sharpe_ratio = (annualized_strategy_return / annualized_strategy_volatility) if annualized_strategy_volatility > 0 else np.nan

    running_max = portfolio_df['Total_Portfolio_Value'].cummax()
    daily_drawdown = (portfolio_df['Total_Portfolio_Value'] - running_max) / running_max
    max_drawdown = daily_drawdown.min()

    metrics = {
        "Initial Capital": portfolio_df['Cash'].iloc[0],
        "Final Portfolio Value": portfolio_df['Total_Portfolio_Value'].iloc[-1],
        "Strategy Cumulative Return (%)": cumulative_strategy_return * 100,
        "Buy & Hold Cumulative Return (%)": cumulative_asset_return * 100,
        "Annualized Strategy Return (%)": annualized_strategy_return * 100,
        "Annualized Buy & Hold Return (%)": annualized_asset_return * 100,
        "Annualized Strategy Volatility (%)": annualized_strategy_volatility * 100,
        "Annualized Buy & Hold Volatility (%)": annualized_asset_volatility * 100,
        "Sharpe Ratio": sharpe_ratio,
        "Max Drawdown (%)": max_drawdown * 100
    }
    return metrics

# --- Example usage (for testing this module independently) ---
if __name__ == "__main__":
    print("--- Testing backtester.py ---")

    # Create dummy data that resembles output from strategy.py
    data = {
        'Close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101],
        'Position': [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    }
    dates = pd.to_datetime(pd.date_range(start='2024-01-01', periods=len(data['Close'])))
    test_df_for_backtest = pd.DataFrame(data, index=dates)

    print("\nDataFrame for backtest (first 5 rows):")
    print(test_df_for_backtest.head())

    initial_cap = 100000.0
    print(f"\nRunning backtest with initial capital: ${initial_cap:,.2f}...")
    portfolio_results = run_backtest(test_df_for_backtest, initial_cap)

    if not portfolio_results.empty:
        print("\nPortfolio Results (last 5 rows):")
        print(portfolio_results.tail())

        print("\nPerformance Metrics:")
        metrics = calculate_performance_metrics(portfolio_results)
        if "Error" in metrics:
            print(metrics["Error"])
        else:
            for key, value in metrics.items():
                if isinstance(value, float) and not np.isnan(value): # Check for float and not NaN before formatting
                    print(f"{key}: {value:,.2f}")
                else:
                    print(f"{key}: {value}")
    else:
        print("Backtest failed or returned empty results.")

    print("\n--- backtester.py testing complete ---")