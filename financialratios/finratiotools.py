import requests
import time
import pandas as pd
from langchain.tools import tool
from typing import Dict, Any, Annotated

headers = {'User-Agent': "dshah@sd5.me"}

def fetch_company_data() -> pd.DataFrame:
    """
    Fetches and processes company ticker data from SEC's website.

    Returns:
        pd.DataFrame: A DataFrame containing company tickers and associated CIK values.
    """
    response = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=headers
    )
    data = response.json()
    company_data = pd.DataFrame.from_dict(data, orient='index')

    # Ensure CIK values are zero-padded to 10 digits
    company_data['cik_str'] = company_data['cik_str'].astype(str).str.zfill(10)
    company_data = company_data.set_index('ticker')

    return company_data


# Global variables to store company data
company_cik_data = fetch_company_data()
company_facts_data = {}


@tool
def refresh_company_cik_data() -> str:
    """
    Refreshes the global company data from the SEC API.

    Returns:
        str: A success message confirming the update.
    """
    global company_cik_data
    company_cik_data = fetch_company_data()
    return "Company cik data refreshed successfully."


@tool
def get_cik_from_ticker(ticker: str) -> str:
    """
    Retrieves the CIK value for a given company ticker.

    Args:
        ticker (str): The ticker symbol of the company.

    Returns:
        str: The CIK value associated with the ticker.
    """
    if ticker not in company_cik_data.index:
        raise ValueError(f"Ticker '{ticker}' not found.")
    return company_cik_data.loc[ticker]['cik_str']



@tool
def refresh_company_facts_data(cik: str) -> str:
    """
    Retrieves company facts data from the SEC using the given CIK.

    Args:
        cik (str): The CIK value of the company.

    Returns:
        str: A success message confirming the update.
    """
    global company_facts_data, headers
    response = requests.get(
        f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
        headers=headers
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch data for CIK {cik}.")
    company_facts_data[cik] = {}
    company_facts_data[cik]['data'] = response.json()
    company_facts_data[cik]['timestamp'] = time.time()
    return "Company facts data refreshed successfully."


@tool
def check_company_facts_data(cik: str) -> bool:
    """
    Check if Company Facts Data is Available.

    Args:
        cik (str): The CIK value of the company.

    Returns:
        bool: True if available, False if not available
    """
    global company_facts_data

    if (cik in company_facts_data) and ((company_facts_data[cik]["timestamp"] - time.time()) < 86400):
        return True

    return False 


@tool
def calculate_roe(cik: str) -> float:
    """
    Computes the return on equity (ROE) from SEC company facts data.
    It has global access to Company Facts Data.

    Args:
        cik (str): The CIK value of the company.

    Returns:
        float: The calculated ROE, or 0 if data is insufficient.
    """
    global company_facts_data
    
    try:
        net_income_data = company_facts_data[cik]['data']['facts']['us-gaap']['NetIncomeLoss']['units']['USD']
        equity_data = company_facts_data[cik]['data']['facts']['us-gaap']['StockholdersEquity']['units']['USD']

        def get_latest_data(form_type: str):
            """
            Fetches net income and equity values for the specified form type (e.g., '10-K', '10-Q').

            Args:
                form_type (str): The type of form to search for (e.g., '10-K', '10-Q').

            Returns:
                tuple: Net income and equity values if found; otherwise, (0, 0).
            """
            accn = None
            net_income, equity = 0, 0

            for report in reversed(net_income_data):
                if report['form'] == form_type:
                    accn = report['accn']
                    net_income = report['val']
                    break

            if accn:
                for report in reversed(equity_data):
                    if report['accn'] == accn:
                        equity = report['val']
                        break

            return net_income, equity

        # Prioritize '10-K' and fallback to '10-Q' if needed
        net_income, equity = get_latest_data('10-K')
        if not (net_income and equity):
            net_income, equity = get_latest_data('10-Q')

        
        if net_income and equity:
            return net_income / equity
        
        return 0

    except KeyError as e:
        raise ValueError(f"Missing data in company facts: {e}")