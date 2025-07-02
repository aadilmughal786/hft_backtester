# QuantView Backtester

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://aadil-hft-backtester.streamlit.app/)
[![GitHub last commit](https://img.shields.io/github/last-commit/aadil-m/hft-backtester?color=green)](https://github.com/aadil-m/hft-backtester)
[![GitHub stars](https://img.shields.io/github/stars/aadil-m/hft-backtester?style=social)](https://github.com/aadil-m/hft-backtester)

An interactive web application built with [Streamlit](https://streamlit.io/) to backtest a Simple Moving Average (SMA) Crossover trading strategy on historical stock data. This project emphasizes modular design, best development practices, and interactive data visualization.

## ✨ Features

- **Historical Data Fetching:** Seamlessly fetches daily historical stock data using `yfinance`.
- **SMA Calculation:** Computes short and long Simple Moving Averages.
- **Signal Generation:** Generates buy/sell signals based on SMA crossovers.
- **Backtesting Engine:** Simulates portfolio performance with a given initial capital, tracking holdings and cash.
- **Performance Metrics:** Calculates key metrics like Cumulative Return, Annualized Return, Volatility, Sharpe Ratio, and Max Drawdown.
- **Interactive Visualizations:**
  - Plotly chart showing stock price, SMAs, and trade entry/exit points.
  - Plotly chart comparing strategy portfolio value against a Buy & Hold benchmark.
- **User-Friendly Interface:** Intuitive sidebar controls for ticker, SMA windows, capital, and date range.
- **Performance Optimized:** Utilizes Streamlit's `@st.cache_data` for efficient data handling and faster user experience.

## 🚀 Live Application

Experience the **QuantView Backtester** live in your browser:
[https://aadil-hft-backtester.streamlit.app/](https://aadil-hft-backtester.streamlit.app/)

## 🔧 Local Setup & Run

Follow these steps to set up and run the application on your local machine.

### Prerequisites

- Python 3.8+
- `pip` (Python package installer)
- `git` (Version control system)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/aadil-m/hft-backtester.git](https://github.com/aadil-m/hft-backtester.git)
    cd hft-backtester
    ```

2.  **Create and activate a virtual environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.

    ```bash
    python -m venv .venv
    ```

    - **On macOS/Linux:**
      ```bash
      source .venv/bin/activate
      ```
    - **On Windows (Command Prompt):**
      ```cmd
      .venv\Scripts\activate.bat
      ```
    - **On Windows (PowerShell):**
      ```powershell
      .venv\Scripts\Activate.ps1
      ```

3.  **Install dependencies:**
    All required libraries are listed in `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Ensure your virtual environment is active.**
2.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```
    This command will open the application in your default web browser (usually at `http://localhost:8501`).

## 📁 Project Structure

The project follows a modular `src` layout for clear separation of concerns:

```

hft\_backtester/
├── src/                      \# Core Python application logic
│   ├── data\_handler.py       \# Fetches and preprocesses market data
│   ├── strategy.py           \# Calculates indicators and generates trading signals
│   ├── backtester.py         \# Simulates trades and evaluates performance
│   ├── visualization.py      \# Creates interactive Plotly charts
│   ├── utils.py              \# General utility functions (e.g., formatters, date helpers)
│   └── **init**.py           \# Makes 'src' a Python package
├── .streamlit/               \# Streamlit-specific configurations
│   └── secrets.toml          \# For secrets on Streamlit Community Cloud (local copy excluded)
├── .env                      \# Local environment variables (NOT committed to Git)
├── .gitignore                \# Specifies files/folders to ignore in Git
├── app.py                    \# Main Streamlit application entry point (UI orchestration)
├── requirements.txt          \# List of Python dependencies
├── README.md                 \# Project description and instructions (this file)
└── tests/                    \# (Optional) For unit and integration tests
└── ...

```

## ☁️ Deployment

This application is deployed on [Streamlit Community Cloud](https://share.streamlit.io/). The deployment process is automated directly from this GitHub repository. Any pushes to the `main` branch will automatically trigger a redeployment.

## 🛣️ Future Enhancements

* **More Trading Strategies:** Implement additional technical analysis strategies (e.g., RSI, MACD, Bollinger Bands).
* **Advanced Backtesting:** Incorporate transaction costs, slippage, and more sophisticated order execution models.
* **Machine Learning Integration:** Explore ML models for signal generation or risk prediction.
* **Multi-Asset Portfolio:** Allow backtesting on portfolios of multiple assets.
* **Real-time Data (Simulated):** Connect to a WebSocket API for simulated real-time data visualization.
* **User Authentication:** For saving strategies or personalized dashboards.
* **Improved UI/UX:** More interactive elements, dashboards, and custom styling.

---

## 🤝 Contribution

Feel free to fork this repository, open issues, or submit pull requests.

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
