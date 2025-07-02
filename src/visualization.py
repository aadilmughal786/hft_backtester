# hft_backtester/src/visualization.py

import pandas as pd
import numpy as np # Make sure numpy is imported for np.zeros, np.linspace etc.
import plotly.graph_objects as go
from plotly.subplots import make_subplots # Not strictly used yet, but good to have if needed for subplots later

def plot_price_and_smas(df: pd.DataFrame, short_window: int, long_window: int, ticker: str) -> go.Figure:
    """
    Generates an interactive Plotly chart showing Close price, SMAs, and trade signals.

    Args:
        df (pd.DataFrame): DataFrame containing 'Close', 'SMA_Short', 'SMA_Long',
                           'Signal', and 'Position' columns.
                           Must have a DatetimeIndex.
        short_window (int): The period of the short SMA.
        long_window (int): The period of the long SMA.
        ticker (str): The ticker symbol for the chart title.

    Returns:
        go.Figure: A Plotly Figure object with the price chart.
    """
    required_cols = ['Close', 'SMA_Short', 'SMA_Long', 'Signal', 'Position']
    if df.empty or not all(col in df.columns for col in required_cols):
        print("Warning: Insufficient data or columns for price and SMA plot.")
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5, text="No valid data available to plot Price and SMAs.", showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title="Error: Price and SMAs Plot")
        return fig

    fig = go.Figure()

    # Add Close Price trace
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'],
        mode='lines',
        name='Close Price',
        line=dict(color='lightgray', width=1),
        hovertemplate='<b>Date:</b> %{x}<br><b>Price:</b> %{y:.2f}<extra></extra>' # Custom hover info
    ))

    # Add Short SMA trace
    fig.add_trace(go.Scatter(
        x=df.index, y=df[f'SMA_Short'],
        mode='lines',
        name=f'SMA ({short_window})',
        line=dict(color='blue', width=2),
        hovertemplate='<b>Date:</b> %{x}<br><b>SMA:</b> %{y:.2f}<extra></extra>'
    ))

    # Add Long SMA trace
    fig.add_trace(go.Scatter(
        x=df.index, y=df[f'SMA_Long'],
        mode='lines',
        name=f'SMA ({long_window})',
        line=dict(color='orange', width=2),
        hovertemplate='<b>Date:</b> %{x}<br><b>SMA:</b> %{y:.2f}<extra></extra>'
    ))

    # Add Buy Signals
    # Filter only rows where Signal is exactly 1.0 (buy)
    buy_signals = df[df['Signal'] == 1.0]
    if not buy_signals.empty:
        fig.add_trace(go.Scatter(
            x=buy_signals.index, y=buy_signals['Close'],
            mode='markers',
            marker=dict(symbol='triangle-up', size=10, color='green'),
            name='Buy Signal',
            hovertemplate='<b>Buy Signal</b><br><b>Date:</b> %{x}<br><b>Price:</b> %{y:.2f}<extra></extra>'
        ))

    # Add Sell Signals
    # Filter only rows where Signal is exactly -1.0 (sell)
    sell_signals = df[df['Signal'] == -1.0]
    if not sell_signals.empty:
        fig.add_trace(go.Scatter(
            x=sell_signals.index, y=sell_signals['Close'],
            mode='markers',
            marker=dict(symbol='triangle-down', size=10, color='red'),
            name='Sell Signal',
            hovertemplate='<b>Sell Signal</b><br><b>Date:</b> %{x}<br><b>Price:</b> %{y:.2f}<extra></extra>'
        ))

    fig.update_layout(
        title=f'{ticker} Price, Simple Moving Averages, and Trade Signals',
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='x unified', # Shows all trace data at current x-value
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def plot_portfolio_performance(portfolio_df: pd.DataFrame, initial_capital: float, ticker: str) -> go.Figure:
    """
    Generates an interactive Plotly chart showing portfolio value vs. Buy & Hold benchmark.

    Args:
        portfolio_df (pd.DataFrame): DataFrame containing 'Total_Portfolio_Value' and
                                     'Cumulative_Asset_Return' (for benchmark).
                                     Must have a DatetimeIndex.
        initial_capital (float): The initial capital used for backtesting.
        ticker (str): The ticker symbol for the chart title.

    Returns:
        go.Figure: A Plotly Figure object with the portfolio performance chart.
    """
    required_cols = ['Total_Portfolio_Value', 'Cumulative_Asset_Return']
    if portfolio_df.empty or not all(col in portfolio_df.columns for col in required_cols):
        print("Warning: Insufficient data or columns for portfolio performance plot.")
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5, text="No valid data available to plot Portfolio Performance.", showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title="Error: Portfolio Performance Plot")
        return fig

    fig = go.Figure()

    # Add Strategy Portfolio Value
    fig.add_trace(go.Scatter(
        x=portfolio_df.index, y=portfolio_df['Total_Portfolio_Value'],
        mode='lines',
        name='Strategy Portfolio Value',
        line=dict(color='green', width=2),
        hovertemplate='<b>Date:</b> %{x}<br><b>Portfolio:</b> %{y:,.2f}<extra></extra>'
    ))

    # Add Buy & Hold Benchmark
    # Calculate Buy & Hold value: initial capital * (1 + Cumulative_Asset_Return)
    # Ensure Cumulative_Asset_Return is a Series to perform vectorized operation
    buy_hold_value = initial_capital * (1 + portfolio_df['Cumulative_Asset_Return'])
    fig.add_trace(go.Scatter(
        x=portfolio_df.index, y=buy_hold_value,
        mode='lines',
        name='Buy & Hold Benchmark',
        line=dict(color='purple', width=2, dash='dash'),
        hovertemplate='<b>Date:</b> %{x}<br><b>Buy & Hold:</b> %{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'{ticker} Portfolio Performance: Strategy vs. Buy & Hold',
        xaxis_title='Date',
        # Dynamic currency based on ticker suffix for Indian stocks (NSE)
        yaxis_title='Portfolio Value (INR)' if ticker.endswith('.NS') else 'Portfolio Value ($)',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

# --- Example usage (for testing this module independently) ---
if __name__ == "__main__":
    print("--- Testing visualization.py ---")

    # Create dummy data resembling output from strategy.py and backtester.py
    # Ensure this data is complete and has no NaNs in critical columns for plotting.
    
    num_days = 100 # Increased number of days for better visualization
    dates = pd.to_datetime(pd.date_range(start='2024-01-01', periods=num_days))
    
    # Generate more realistic-looking dummy price data
    np.random.seed(42) # For reproducibility of dummy data
    prices = 100 + np.cumsum(np.random.randn(num_days) * 0.5) # A random walk for prices
    
    dummy_close = pd.Series(prices, index=dates)

    # Calculate dummy SMAs - ensure min_periods=1 for early data points
    dummy_sma_short = dummy_close.rolling(window=10, min_periods=1).mean()
    dummy_sma_long = dummy_close.rolling(window=30, min_periods=1).mean()

    # Generate more dynamic dummy signals and positions
    # We'll create a simple crossover behavior for signals
    dummy_crossover_state = (dummy_sma_short > dummy_sma_long).astype(int)
    dummy_signal = dummy_crossover_state.diff().fillna(0) # 1 for buy, -1 for sell
    dummy_signal[dummy_signal > 0] = 1.0
    dummy_signal[dummy_signal < 0] = -1.0
    
    # Calculate dummy position based on the crossover state (lagged to avoid look-ahead bias)
    # If SMA_Short > SMA_Long, position is 1 (long); otherwise 0 (cash)
    dummy_position = np.where(dummy_sma_short > dummy_sma_long, 1.0, 0.0)
    dummy_position = pd.Series(dummy_position, index=dates).shift(1).fillna(0.0) # Shift and fill

    dummy_df = pd.DataFrame({
        'Close': dummy_close,
        'SMA_Short': dummy_sma_short,
        'SMA_Long': dummy_sma_long,
        'Signal': dummy_signal,
        'Position': dummy_position
    })
    
    # Important: Drop any remaining NaNs that might affect plotting
    # For robust SMAs with min_periods=1, there should be fewer NaNs.
    # However, if actual data has NaNs after fetching or signal generation,
    # backtester and visualization functions should get cleaned data.
    dummy_df = dummy_df.dropna() 

    print("\nDummy DataFrame for plotting (first 5 rows):")
    print(dummy_df.head())
    print("\nDummy DataFrame info:")
    dummy_df.info()
    print("\nMissing values in dummy DataFrame:")
    print(dummy_df.isnull().sum())


    print("\nPlotting Price and SMAs...")
    fig_price = plot_price_and_smas(dummy_df, 10, 30, "TEST_TICKER_FOR_PLOT")
    fig_price.show() # This will open the plot in your default browser or viewer

    # Create dummy portfolio data for testing performance plot
    initial_cap_test = 100000.0
    
    # Simulate portfolio value and asset returns based on dummy prices
    dummy_daily_asset_return = dummy_df['Close'].pct_change().fillna(0)
    dummy_cumulative_asset_return = (1 + dummy_daily_asset_return).cumprod() - 1
    
    # Simple simulation for portfolio value (e.g., if we just followed position on dummy data)
    # This is a simplified version; the actual backtester gives you Total_Portfolio_Value
    dummy_strategy_daily_return = dummy_df['Position'] * dummy_daily_asset_return
    dummy_total_portfolio_value = initial_cap_test * (1 + dummy_strategy_daily_return).cumprod()
    
    # Ensure initial value is correct
    if not dummy_total_portfolio_value.empty:
        dummy_total_portfolio_value.iloc[0] = initial_cap_test # Start with initial capital


    dummy_portfolio_df = pd.DataFrame({
        'Total_Portfolio_Value': dummy_total_portfolio_value,
        'Cumulative_Asset_Return': dummy_cumulative_asset_return
    }, index=dummy_df.index) # Use the same index as dummy_df
    
    dummy_portfolio_df = dummy_portfolio_df.dropna() # Drop NaNs if any after calculation

    print("\nDummy Portfolio DataFrame for plotting (first 5 rows):")
    print(dummy_portfolio_df.head())
    print("\nMissing values in dummy Portfolio DataFrame:")
    print(dummy_portfolio_df.isnull().sum())

    print("\nPlotting Portfolio Performance...")
    fig_portfolio = plot_portfolio_performance(dummy_portfolio_df, initial_cap_test, "TEST_TICKER_FOR_PLOT")
    fig_portfolio.show() # This will open the plot in your default browser or viewer

    print("\n--- visualization.py testing complete ---")