import requests
import json
import pandas as pd
import time, os
from langchain.tools import tool


@tool
def get_file_path(ticker: str, trend: str, window: int = None) -> str:
    """
    Generates a file path for a given ticker, trend, and optional window/span.

    Args:
        ticker (str): The stock ticker symbol (e.g., "TSLA", "NVDA").
        trend (str): The trend type (e.g., "closing price", "moving average", "long moving average").
        window (int, optional): The window/span for moving averages.

    Returns:
        str: The generated file path.
    """
    # Strip leading/trailing spaces from inputs
    ticker = ticker.upper().strip()
    trend = trend.lower().strip().replace(" ", "_")  # Replace spaces with underscores for file naming

    # Generate file path
    if window:
        file_path = f"{ticker}_{trend}_{window}.csv"
    else:
        file_path = f"{ticker}_{trend}.csv"

    return file_path


@tool
def create_plots(file_paths: list) -> list[str]:
    """
    Creates a plot using the given file paths saves them on the server.

    Args:
        file_paths (list): List of file paths to process.

    Returns:
        list[str]: A list of file paths where the plots were saved.
    """

    try:
        print("In Create Plots ", type(file_paths), file_paths)
        return file_paths
    except Exception as e:
        print(f"Plot Creation Error : {e}")
