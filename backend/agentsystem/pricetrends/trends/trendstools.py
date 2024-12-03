import requests
import json
import pandas as pd
import time, os
import yfinance as yf
from langchain.tools import tool


stock_data = {}  
root_dir = os.path.join('data', 'csv')

@tool
def refresh_stock_data(ticker: str) -> str:
    """
    Retrieves company stock price data from yfinance using the given ticker.

    Args:
        ticker (str): The ticker symbol of the company.

    Returns:
        str: A success message confirming the update.
    """
    global stock_data, root_dir

    ticker_stock = yf.download(ticker, period="6mo")  # 6 months of data
    if ticker_stock.empty:
        raise ValueError(f"No data found for ticker: {ticker}")
    
    ticker_stock.index = ticker_stock.index.astype(str)
    
    stock_data[ticker] = {}
    stock_data[ticker]["last_update_time"] =  time.time()
    stock_data[ticker]["data"] = ticker_stock

    return "Stock data refreshed successfully."


@tool
def check_stock_data(ticker: str) -> bool:
    """
    Check if Company Stock Data is Available.

    Args:
        ticker (str): The ticker symbol of the company.

    Returns:
        bool: True if available, False if not available.
    """
    global stock_data, root_dir

    if (ticker in stock_data) and ((stock_data[ticker]["last_update_time"] - time.time()) < 86400):
        return True

    return False 


@tool
def get_closing_price(ticker: str) -> str:
    """
    Retrieves a stock's closing prices and saves them to the server.

    Args:
        ticker (str): The stock ticker symbol for which to get the closing prices.

    Returns:
        str: A success message confirming the update.

    """
    try:
        closing_price = stock_data[ticker]["data"]['Close']
        closing_price.columns = ['Values']
        save_path = os.path.join(root_dir, f"{ticker.upper()}_closing_price.csv")
        closing_price.to_csv(save_path)

        return f"Got Closing Prices for {ticker}"

    except KeyError as e:
        raise ValueError(f"Missing stock price data: {e}")
        


@tool
def get_moving_average(ticker: str, window: int = 15) -> str:
    """
    Calculate the moving average of a stock's closing prices over a specified window and saves them to the server.

    This tool fetches historical stock closing prices and computes a moving average 
    for the specified rolling window size.

    Args:
        ticker (str): The stock ticker symbol for which to calculate the moving average.
        window (int): The size (days) of the rolling window to compute the moving average. This is number of days. 

    Returns:
        str: A success message confirming the update.

    """
    try:
        closing_price = stock_data[ticker]["data"]['Close']
        moving_average = closing_price.rolling(window=window).mean()
        moving_average.columns = ['Values']
        save_path = os.path.join(root_dir, f"{ticker.upper()}_moving_average_{window}.csv")
        moving_average.to_csv(save_path)

        return f"Got Moving Average with window {window} for {ticker}"

    except KeyError as e:
        raise ValueError(f"Missing stock price data: {e}")


@tool
def get_short_moving_average(ticker: str) -> str:
    """
    Calculate the short moving average (SMA) of a stock's closing prices over a short window and saves them to the server.

    This tool is specialized to compute a moving average over a predefined short window of 10 periods. 
    It is useful for identifying short-term trends in the stock's performance.


    Args:
        ticker (str): The stock ticker symbol for which to calculate the moving average.

    Returns:
        str: A success message confirming the update.

    """
    try:
        window = 10
        closing_price = stock_data[ticker]["data"]['Close']
        moving_average = closing_price.rolling(window=window).mean()
        moving_average.columns = ['Values']
        save_path = os.path.join(root_dir, f"{ticker.upper()}_short_moving_average.csv")
        moving_average.to_csv(save_path)

        return f"Got Short Moving Average for {ticker}"


    except KeyError as e:
        raise ValueError(f"Missing stock price data: {e}") 
    

@tool
def get_long_moving_average(ticker: str) -> str:
    """
    Calculate the long moving average (LMA) of a stock's closing prices over a fixed long window and saves them to the server.

    This tool computes the moving average over a predefined long window of 50 periods, 
    which is useful for identifying long-term trends in stock performance.

    Args:
        ticker (str): The stock ticker symbol for which to calculate the long moving average.

    Returns:
        str: A success message confirming the update.

    """
    try:
        window = 50
        closing_price = stock_data[ticker]["data"]['Close']
        moving_average = closing_price.rolling(window=window).mean()
        moving_average.columns = ['Values']
        save_path = os.path.join(root_dir, f"{ticker.upper()}_long_moving_average.csv")
        moving_average.to_csv(save_path)

        return f"Got Long Moving Average for {ticker}"


    except KeyError as e:
        raise ValueError(f"Missing stock price data: {e}")


@tool
def get_exponential_moving_average(ticker: str, span: int) -> str:
    """
    Calculate the exponential moving average (EMA) of a stock's closing prices and saves them to the server.

    This tool computes the exponential moving average, which gives more weight 
    to recent data points, making it more responsive to recent price changes. 
    The user can specify the "span" parameter to control the degree of smoothing.

    Args:
        ticker (str): The stock ticker symbol for which to calculate the EMA.
        span (int): The span parameter for the EMA, representing the smoothing factor.
    
    Returns:
        str: A success message confirming the update.

    """
    try:
        closing_price = stock_data[ticker]["data"]['Close']
        exponential_moving_average = closing_price.ewm(span=span, adjust=False).mean()
        exponential_moving_average.columns = ['Values']
        save_path = os.path.join(root_dir, f"{ticker.upper()}_exponential_moving_average_{span}.csv")
        exponential_moving_average.to_csv(save_path)

        return f"Got Exponential Moving Average with span {span} for {ticker}"


    except KeyError as e:
        raise ValueError(f"Missing stock price data: {e}")

