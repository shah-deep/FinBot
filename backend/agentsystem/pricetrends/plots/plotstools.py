import requests
import json
import pandas as pd
import time, os
import matplotlib.pyplot as plt
from langchain.tools import tool

source_dir = os.path.join('data', 'csv')
output_dir = os.path.join('data', 'img')

@tool
def get_file_path(ticker: str, trend: str, window: int = 0) -> str:
    """
    Generates a file path for a given ticker, trend, and optional window/span.

    Args:
        ticker (str): The stock ticker symbol (e.g., "TSLA", "NVDA").
        trend (str): The trend type (full name only) (e.g., "closing price", "moving average", "long moving average", "exponential moving average").
        window (int, optional): The window or span for moving averages. Only take integer part if given as days.

    Returns:
        str: The generated file path.
    """
    # Strip leading/trailing spaces from inputs
    ticker = ticker.upper().strip()
    trend = trend.lower().strip().replace(" ", "_")  # Replace spaces with underscores for file naming

    # Generate file path
    if window and (("short" not in trend) and ("long" not in trend)):
        file_path = f"{ticker}_{trend}_{window}.csv"
    else:
        file_path = f"{ticker}_{trend}.csv"

    return file_path


@tool
def create_plots(file_paths: list) -> str:
    """
    Creates a plot using the given file paths saves them on the server.

    Args:
        file_paths (list): List of file paths to process.

    Returns:
        str: The file path where the plot was saved.
    """

    try:
        plt.figure(figsize=(10, 10))
        file_name_parts = []

        for file_path in file_paths:
            df = pd.read_csv(os.path.join(source_dir, file_path))
            
            df['Date'] = pd.to_datetime(df['Date'])  # Ensure Date is in datetime format
            df['Values'] = df['Values'].astype(float)  # Ensure Values are floats
            
            label_parts = file_path.replace('.csv', '').title().split("_")
            label_parts[0] = label_parts[0].upper()
            label =  ' '.join(label_parts)
            file_name_parts.append(''.join(label_parts))

            plt.plot(df['Date'], df['Values'], label=label)

        plt.xlabel('Time', fontsize=16)
        plt.ylabel('Stock Price', fontsize=16)
        plt.grid(visible=True)
        plt.legend()
        plt.tight_layout()

        image_file_name = '_'.join(file_name_parts) + '.png'
        plt.savefig(os.path.join(output_dir, image_file_name))

        return image_file_name
    
    except Exception as e:
        print(f"Plot Creation Error : {e}, Retry.")
