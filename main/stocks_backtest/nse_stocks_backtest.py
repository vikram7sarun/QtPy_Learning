import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import requests
import json
from typing import Dict, List


class DhanAPI:
    def __init__(self, client_id: str, access_token: str):
        """
        Initialize Dhan API client

        Parameters:
        client_id (str): Your Dhan client ID
        access_token (str): Your Dhan access token
        """
        self.client_id = client_id
        self.access_token = access_token
        self.base_url = "https://api.dhan.co"
        self.headers = {
            'access-token': access_token,
            'client-id': client_id,
            'Content-Type': 'application/json'
        }

    def get_historical_data(self, symbol: str, from_date: str, to_date: str, interval: str = '1d') -> pd.DataFrame:
        """
        Fetch historical data from Dhan API

        Parameters:
        symbol (str): Trading symbol (e.g., 'RELIANCE')
        from_date (str): Start date in YYYY-MM-DD format
        to_date (str): End date in YYYY-MM-DD format
        interval (str): Time interval ('1d' for daily)

        Returns:
        pd.DataFrame: Historical price data
        """
        endpoint = f"{self.base_url}/charts/historical"

        # Convert dates to required format
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')

        payload = {
            "symbol": symbol,
            "exchangeSegment": "NSE_EQ",
            "instrument": "EQUITY",
            "fromDate": from_date_obj.strftime('%d-%m-%Y'),
            "toDate": to_date_obj.strftime('%d-%m-%Y'),
            "interval": interval
        }

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # Convert response to DataFrame
            df = pd.DataFrame(data['data'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # Rename columns to match our backtester
            df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }, inplace=True)

            return df

        except requests.exceptions.RequestException as e:
            print(f"Error fetching historical data: {str(e)}")
            return pd.DataFrame()


class NSEBacktester:
    def __init__(self, dhan_api: DhanAPI, symbol: str, start_date: str, end_date: str, initial_capital: float = 100000):
        """
        Initialize the backtester with Dhan API and stock details

        Parameters:
        dhan_api (DhanAPI): Initialized Dhan API client
        symbol (str): NSE stock symbol
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        initial_capital (float): Starting capital for backtesting
        """
        self.dhan_api = dhan_api
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.data = None
        self.signals = pd.DataFrame()

    def fetch_data(self) -> bool:
        """Fetch historical data using Dhan API"""
        self.data = self.dhan_api.get_historical_data(
            self.symbol,
            self.start_date,
            self.end_date
        )
        return not self.data.empty

    def calculate_indicators(self):
        """Calculate technical indicators"""
        # Simple Moving Averages
        self.data['SMA20'] = self.data['Close'].rolling(window=20).mean()
        self.data['SMA50'] = self.data['Close'].rolling(window=50).mean()

        # RSI
        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = self.data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = self.data['Close'].ewm(span=26, adjust=False).mean()
        self.data['MACD'] = exp1 - exp2
        self.data['Signal_Line'] = self.data['MACD'].ewm(span=9, adjust=False).mean()

        # Volume indicators
        self.data['Volume_SMA20'] = self.data['Volume'].rolling(window=20).mean()

    def generate_signals(self):
        """Generate trading signals based on indicators"""
        self.signals = pd.DataFrame(index=self.data.index)

        # Initialize signals
        self.signals['Signal'] = 0

        # Generate buy signals (1) and sell signals (-1)
        # Enhanced buy conditions
        buy_condition = (
                (self.data['SMA20'] > self.data['SMA50']) &
                (self.data['RSI'] < 70) &
                (self.data['MACD'] > self.data['Signal_Line']) &
                (self.data['Volume'] > self.data['Volume_SMA20'])  # Volume confirmation
        )

        # Enhanced sell conditions
        sell_condition = (
                (self.data['SMA20'] < self.data['SMA50']) |
                (self.data['RSI'] > 70) |
                (self.data['MACD'] < self.data['Signal_Line'])
        )

        self.signals.loc[buy_condition, 'Signal'] = 1
        self.signals.loc[sell_condition, 'Signal'] = -1

    def backtest(self) -> Dict:
        """Execute backtest and calculate performance metrics"""
        self.signals['Position'] = self.signals['Signal'].fillna(0)
        self.signals['Price'] = self.data['Close']

        # Calculate returns
        self.signals['Returns'] = self.data['Close'].pct_change()
        self.signals['Strategy_Returns'] = self.signals['Position'].shift(1) * self.signals['Returns']

        # Calculate cumulative returns
        self.signals['Cumulative_Market_Returns'] = (1 + self.signals['Returns']).cumprod()
        self.signals['Cumulative_Strategy_Returns'] = (1 + self.signals['Strategy_Returns']).cumprod()

        # Calculate portfolio value
        self.signals['Portfolio_Value'] = self.initial_capital * self.signals['Cumulative_Strategy_Returns']

        # Calculate performance metrics
        total_return = self.signals['Cumulative_Strategy_Returns'].iloc[-1] - 1
        market_return = self.signals['Cumulative_Market_Returns'].iloc[-1] - 1
        sharpe_ratio = np.sqrt(252) * (self.signals['Strategy_Returns'].mean() / self.signals['Strategy_Returns'].std())
        max_drawdown = (self.signals['Portfolio_Value'] / self.signals['Portfolio_Value'].cummax() - 1).min()

        # Calculate additional metrics
        win_rate = len(self.signals[self.signals['Strategy_Returns'] > 0]) / len(
            self.signals[self.signals['Strategy_Returns'] != 0])
        avg_profit = self.signals[self.signals['Strategy_Returns'] > 0]['Strategy_Returns'].mean()
        avg_loss = self.signals[self.signals['Strategy_Returns'] < 0]['Strategy_Returns'].mean()

        return {
            'Total Return': f"{total_return:.2%}",
            'Market Return': f"{market_return:.2%}",
            'Sharpe Ratio': f"{sharpe_ratio:.2f}",
            'Max Drawdown': f"{max_drawdown:.2%}",
            'Win Rate': f"{win_rate:.2%}",
            'Average Profit': f"{avg_profit:.2%}",
            'Average Loss': f"{avg_loss:.2%}",
            'Final Portfolio Value': f"₹{self.signals['Portfolio_Value'].iloc[-1]:,.2f}"
        }

    def plot_results(self):
        """Plot backtest results"""
        plt.style.use('seaborn')
        fig = plt.figure(figsize=(15, 12))

        # Plot 1: Portfolio Value
        ax1 = plt.subplot(3, 1, 1)
        self.signals['Portfolio_Value'].plot(ax=ax1, label='Portfolio Value')
        ax1.set_title('Portfolio Value Over Time')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Value (₹)')
        ax1.legend()

        # Plot 2: Price and Signals
        ax2 = plt.subplot(3, 1, 2)
        self.data['Close'].plot(ax=ax2, label='Stock Price', alpha=0.7)
        self.data['SMA20'].plot(ax=ax2, label='SMA20', alpha=0.5)
        self.data['SMA50'].plot(ax=ax2, label='SMA50', alpha=0.5)

        # Plot buy signals
        ax2.plot(self.signals.loc[self.signals['Signal'] == 1].index,
                 self.data['Close'][self.signals['Signal'] == 1],
                 '^', markersize=10, color='g', label='Buy Signal')

        # Plot sell signals
        ax2.plot(self.signals.loc[self.signals['Signal'] == -1].index,
                 self.data['Close'][self.signals['Signal'] == -1],
                 'v', markersize=10, color='r', label='Sell Signal')

        ax2.set_title('Trading Signals')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Price (₹)')
        ax2.legend()

        # Plot 3: Technical Indicators
        ax3 = plt.subplot(3, 1, 3)
        self.data['RSI'].plot(ax=ax3, label='RSI', color='purple')
        ax3.axhline(y=70, color='r', linestyle='--', alpha=0.5)
        ax3.axhline(y=30, color='g', linestyle='--', alpha=0.5)
        ax3.set_title('RSI Indicator')
        ax3.set_xlabel('Date')
        ax3.set_ylabel('RSI')
        ax3.legend()

        plt.tight_layout()
        plt.show()


def run_backtest(dhan_api: DhanAPI, symbol: str, start_date: str, end_date: str, initial_capital: float = 100000):
    """
    Run backtest for a given stock using Dhan API

    Example:"""
    dhan_api = DhanAPI('1103544938', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzMxNDY5OTMwLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMzU0NDkzOCJ9.Eq-pvWo-SHTBVFIQMurvmW5r405vDG3SxZv2TbGRLMl5cXCl7jN6upQ8J9kJ6KBi9u2ousJqU_Cnp4EOOpSDOQ')
    run_backtest(dhan_api, 'RELIANCE', '2023-01-01', '2024-01-01', 100000)

    # Run backtest
    backtest = run_backtest(
        dhan_api=dhan_api,
        symbol='RELIANCE',
        start_date='2023-01-01',
        end_date='2024-01-01',
        initial_capital=100000
    )

    backtester = NSEBacktester(dhan_api, symbol, start_date, end_date, initial_capital)

    if backtester.fetch_data():
        backtester.calculate_indicators()
        backtester.generate_signals()
        results = backtester.backtest()

        print(f"\nBacktest Results for {symbol}:")
        print("=" * 50)
        for metric, value in results.items():
            print(f"{metric}: {value}")

        backtester.plot_results()
        return backtester
    return None