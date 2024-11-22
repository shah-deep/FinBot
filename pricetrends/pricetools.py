import requests
import time
import json
import pandas as pd
import yfinance as yf
from langchain.tools import tool



stock_data = {}  

@tool
def refresh_stock_data(ticker: str) -> str:
    """
    Retrieves company stock price data from yfinance using the given ticker.

    Args:
        ticker (str): The ticker symbol of the company.

    Returns:
        str: A success message confirming the update.
    """
    global stock_data

    ticker_stock = yf.download(ticker, period="1mo")  # 6 months of data
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
        bool: True if available, False if not available
    """
    global stock_data

    if (ticker in stock_data) and ((stock_data[ticker]["last_update_time"] - time.time()) < 86400):
        return True

    return False 


@tool
def get_closing_price(ticker: str) -> dict:
    """
    Retrieve a stock's closing prices.

    Args:
        ticker (str): The stock ticker symbol for which to get the closing prices.

    Returns:
        dict: A dictionary containing:
            - "ticker" (str): The stock ticker symbol.
            - "info" (str): A string describing the calculation.
            - "data" (dict): A dictionary mapping timestamps to their corresponding closing price.
    """
    try:
        closing_price = stock_data[ticker]["data"]['Close']
        original_dict = closing_price.to_dict()
        ticker, data = list(original_dict.items())[0] 
        transformed_dict = {
            "ticker": ticker,
            "info": "Closing Price",
            "data": data
        }
        print("Git Dict")
        return transformed_dict

    except KeyError as e:
        raise ValueError(f"Missing stock price data: {e}")
    finally:
        print("Return done")
        


@tool
def get_moving_average(ticker: str, window: int) -> dict:
    """
    Calculate the moving average of a stock's closing prices over a specified window.

    This tool fetches historical stock closing prices and computes a moving average 
    for the specified rolling window size.

    Args:
        ticker (str): The stock ticker symbol for which to calculate the moving average.
        window (int): The size of the rolling window to compute the moving average.

    Returns:
        dict: A dictionary containing:
            - "ticker" (str): The stock ticker symbol.
            - "info" (str): A string describing the calculation.
            - "data" (dict): A dictionary mapping timestamps to their corresponding moving average values.
    """
    try:
        closing_price = stock_data[ticker]["data"]['Close']
        moving_average = closing_price.rolling(window=window).mean()
        original_dict = moving_average.to_dict()
        ticker, data = list(original_dict.items())[0] 
        transformed_dict = {
            "ticker": ticker,
            "info": f"Moving Average (window={window})",
            "data": data
        }
        
        return transformed_dict

    except KeyError as e:
        raise ValueError(f"Missing stock price data: {e}")


@tool
def get_short_moving_average(ticker: str) -> dict:
    """
    Calculate the short moving average of a stock's closing prices over a short window.

    This tool is specialized to compute a moving average over a predefined short window of 10 periods. 
    It is useful for identifying short-term trends in the stock's performance.


    Args:
        ticker (str): The stock ticker symbol for which to calculate the moving average.

    Returns:
        dict: A dictionary containing:
            - "ticker" (str): The stock ticker symbol.
            - "info" (str): A description of the short moving average calculation.
            - "data" (dict): A dictionary mapping timestamps to their corresponding short moving average values.
    """
    try:
        window = 10
        closing_price = stock_data[ticker]["data"]['Close']
        moving_average = closing_price.rolling(window=window).mean()
        original_dict = moving_average.to_dict()
        ticker, data = list(original_dict.items())[0] 
        transformed_dict = {
            "ticker": ticker,
            "info": f"Short Moving Average",
            "data": data
        }
        
        return transformed_dict

    except KeyError as e:
        raise ValueError(f"Missing stock price data: {e}") 
    

@tool
def get_long_moving_average(ticker: str) -> dict:
    """
    Calculate the long moving average of a stock's closing prices over a fixed long window.

    This tool computes the moving average over a predefined long window of 50 periods, 
    which is useful for identifying long-term trends in stock performance.

    Args:
        ticker (str): The stock ticker symbol for which to calculate the long moving average.

    Returns:
        dict: A dictionary containing:
            - "ticker" (str): The stock ticker symbol.
            - "info" (str): A description of the long moving average calculation.
            - "data" (dict): A mapping of timestamps to their corresponding long moving average values.
    """
    try:
        window = 50
        closing_price = stock_data[ticker]["data"]['Close']
        moving_average = closing_price.rolling(window=window).mean()
        original_dict = moving_average.to_dict()
        ticker, data = list(original_dict.items())[0] 
        transformed_dict = {
            "ticker": ticker,
            "info": "Long Moving Average",
            "data": data
        }
        
        return transformed_dict

    except KeyError as e:
        raise ValueError(f"Missing stock price data: {e}")


@tool
def get_exponential_moving_average(ticker: str, span: int) -> dict:
    """
    Calculate the exponential moving average (EMA) of a stock's closing prices.

    This tool computes the exponential moving average, which gives more weight 
    to recent data points, making it more responsive to recent price changes. 
    The user can specify the "span" parameter to control the degree of smoothing.

    Args:
        ticker (str): The stock ticker symbol for which to calculate the EMA.
        span (int): The span parameter for the EMA, representing the smoothing factor.

    Returns:
        dict: A dictionary containing:
            - "ticker" (str): The stock ticker symbol.
            - "info" (str): A description of the EMA calculation.
            - "data" (dict): A mapping of timestamps to their corresponding EMA values.
    """
    try:
        closing_price = stock_data[ticker]["data"]['Close']
        exponential_moving_average = closing_price.ewm(span=span, adjust=False).mean()
        original_dict = exponential_moving_average.to_dict()
        ticker, data = list(original_dict.items())[0] 
        transformed_dict = {
            "ticker": ticker,
            "info": f"Exponential Moving Average (span={span})",
            "data": data
        }
        
        return transformed_dict

    except KeyError as e:
        raise ValueError(f"Missing stock price data: {e}")

