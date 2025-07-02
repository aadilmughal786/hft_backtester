# hft_backtester/app.py

import streamlit as st
import pandas as pd
from datetime import datetime

# Import functions from your src modules
from src.data_handler import fetch_historical_data
from src.strategy import calculate_smas, generate_signals
from src.backtester import run_backtest, calculate_performance_metrics
from src.visualization import plot_price_and_smas, plot_portfolio_performance
from src.utils import get_default_date_range, format_currency, get_currency_symbol

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="QuantView Backtester",
    page_icon="📈",
    layout="wide", # Use a wide layout for better display of charts
    initial_sidebar_state="expanded" # Keep sidebar open by default
)

st.title("📈 QuantView Backtester")
st.markdown("---") # Visual separator

# --- Caching Data and Calculations for Performance ---
# @st.cache_data decorator caches the output of functions.
# If the input parameters to the cached function are the same,
# Streamlit serves the result from the cache instead of re-running the function.

@st.cache_data
def cached_fetch_data(ticker, start, end, interval):
    """Cached wrapper for fetching historical data."""
    return fetch_historical_data(ticker, start, end, interval)

@st.cache_data
def cached_run_strategy_and_backtest(df, short_window, long_window, initial_capital):
    """Cached wrapper for running strategy and backtest logic."""
    df_smas = calculate_smas(df.copy(), short_window, long_window)
    df_signals = generate_signals(df_smas.copy())
    portfolio_df = run_backtest(df_signals.copy(), initial_capital)
    return df_smas, df_signals, portfolio_df

# --- Sidebar for User Inputs ---
st.sidebar.header("Strategy Parameters")

# Ticker selection
default_ticker = "AAPL" # Default for US stock
# Check if current location is India based on context provided.
# This makes it more user-friendly for you!
# Current context provides India.
if "India" in st.session_state: # This is a placeholder, a real location check would be dynamic
    default_ticker = "RELIANCE.NS" # Default for India

ticker = st.sidebar.text_input("Ticker Symbol", value=default_ticker).strip().upper()

# SMA Window Lengths
short_window = st.sidebar.slider("Short SMA Window (Days)", min_value=10, max_value=100, value=50, step=5)
long_window = st.sidebar.slider("Long SMA Window (Days)", min_value=50, max_value=300, value=200, step=10)

# Initial Capital
initial_capital = st.sidebar.number_input("Initial Capital", min_value=1000.0, max_value=1_000_000_000.0, value=100_000.0, step=1000.0)

# Date Range Selection
default_start_date, default_end_date = get_default_date_range(years_back=5)
start_date_input = st.sidebar.date_input("Start Date", value=default_start_date)
end_date_input = st.sidebar.date_input("End Date", value=default_end_date)

# Interval (for future expansion, currently fixed to '1d' for simplicity of SMA logic)
# For now, we'll keep it simple and assume daily data for this SMA strategy.
# If you want to expand to intraday, you'll need to adapt SMA and backtesting logic for intervals.
# interval = st.sidebar.selectbox("Data Interval", options=['1d', '1h', '30m'], index=0)
interval = '1d' # Fixed for now

# Convert date inputs to string format for yfinance
start_date_str = start_date_input.strftime('%Y-%m-%d')
end_date_str = end_date_input.strftime('%Y-%m-%d')

# --- Main Content Area - Run Backtest Button ---
st.header("Backtest Results")

# Use a button to trigger the backtest, preventing constant re-runs
if st.sidebar.button("Run Backtest"):
    if start_date_input >= end_date_input:
        st.error("Error: Start date must be before end date. Please adjust the dates.")
    elif long_window <= short_window:
        st.error("Error: Long SMA window must be greater than Short SMA window.")
    else:
        # --- Data Fetching ---
        with st.spinner(f"Fetching historical data for {ticker}..."):
            raw_data_df = cached_fetch_data(ticker, start_date_str, end_date_str, interval)
            
            if raw_data_df.empty:
                st.error(f"Could not fetch historical data for {ticker}. Please check the ticker symbol, date range, or try again later.")
                st.info("Ensure the ticker is correct (e.g., 'RELIANCE.NS' for NSE stocks, 'AAPL' for US stocks).")
                st.stop() # Stop execution if no data

        st.success("Data fetched successfully!")
        
        # --- Strategy Calculation and Backtesting ---
        with st.spinner("Running strategy and backtest simulation..."):
            try:
                # Use .copy() when passing DataFrames to cached functions
                # to ensure distinct objects are passed, preventing internal pandas warnings.
                df_with_smas, df_with_signals, portfolio_df = cached_run_strategy_and_backtest(
                    raw_data_df.copy(), short_window, long_window, initial_capital
                )

                if portfolio_df.empty:
                    st.error("Backtest resulted in no valid data. This can happen if there's insufficient data after SMA calculation or signal generation.")
                    st.stop()
                    
                # Ensure all required columns for plotting and metrics are present after backtest
                required_cols_for_plot = ['Close', 'SMA_Short', 'SMA_Long', 'Signal', 'Position']
                if not all(col in df_with_signals.columns for col in required_cols_for_plot):
                    st.error("Error: Missing required columns for plotting price and SMAs after strategy application.")
                    st.stop()

                required_cols_for_portfolio_plot = ['Total_Portfolio_Value', 'Cumulative_Asset_Return']
                if not all(col in portfolio_df.columns for col in required_cols_for_portfolio_plot):
                    st.error("Error: Missing required columns for plotting portfolio performance after backtest.")
                    st.stop()


            except ValueError as ve:
                st.error(f"Strategy/Backtest Error: {ve}. Please check input parameters or data consistency.")
                st.stop()
            except TypeError as te:
                st.error(f"Data Type Error in Strategy/Backtest: {te}. Ensure data is numeric.")
                st.stop()
            except Exception as e:
                st.error(f"An unexpected error occurred during strategy or backtest: {e}")
                st.stop()
        
        st.success("Backtest completed!")
        
        # --- Display Results ---
        st.subheader("Performance Summary")
        metrics = calculate_performance_metrics(portfolio_df)
        
        # Determine currency symbol for display
        currency_symbol = get_currency_symbol(ticker)

        # Display metrics using st.metric for a nice visual summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Initial Capital", value=format_currency(metrics.get("Initial Capital"), currency_symbol))
            st.metric(label="Strategy Annualized Return", value=f"{metrics.get('Annualized Strategy Return (%)', 0.0):.2f}%")
        with col2:
            st.metric(label="Final Portfolio Value", value=format_currency(metrics.get("Final Portfolio Value"), currency_symbol))
            st.metric(label="Buy & Hold Annualized Return", value=f"{metrics.get('Annualized Buy & Hold Return (%)', 0.0):.2f}%")
        with col3:
            st.metric(label="Strategy Cumulative Return", value=f"{metrics.get('Strategy Cumulative Return (%)', 0.0):.2f}%")
            st.metric(label="Strategy Sharpe Ratio", value=f"{metrics.get('Sharpe Ratio', 0.0):.2f}")
        with col4:
            st.metric(label="Buy & Hold Cumulative Return", value=f"{metrics.get('Buy & Hold Cumulative Return (%)', 0.0):.2f}%")
            st.metric(label="Strategy Max Drawdown", value=f"{metrics.get('Max Drawdown (%)', 0.0):.2f}%")

        st.markdown("---")

        # --- Visualizations ---
        st.subheader("Price & SMA Crossover Signals")
        # Ensure df_with_signals is clean (e.g., no NaNs from early SMA calculations that would affect plots)
        fig_price_smas = plot_price_and_smas(df_with_signals.dropna(), short_window, long_window, ticker)
        st.plotly_chart(fig_price_smas, use_container_width=True) # Makes chart responsive to container width

        st.subheader("Portfolio Performance Over Time")
        fig_portfolio_perf = plot_portfolio_performance(portfolio_df.dropna(), initial_capital, ticker)
        st.plotly_chart(fig_portfolio_perf, use_container_width=True)

        # --- Optional: Display Raw DataFrames (for debugging/detailed view) ---
        with st.expander("View Raw Backtest Data"):
            st.dataframe(portfolio_df)

        with st.expander("View Raw Strategy Data (Price, SMAs, Signals)"):
            st.dataframe(df_with_signals)