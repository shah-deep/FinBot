import requests
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


# Global variable to store company data
company_data = fetch_company_data()


@tool
def refresh_company_data() -> str:
    """
    Refreshes the global company data from the SEC API.

    Returns:
        str: A success message confirming the update.
    """
    global company_data
    company_data = fetch_company_data()
    return "Company data refreshed successfully."


@tool
def get_cik_from_ticker(ticker: str) -> str:
    """
    Retrieves the CIK value for a given company ticker.

    Args:
        ticker (str): The ticker symbol of the company.

    Returns:
        str: The CIK value associated with the ticker.
    """
    if ticker not in company_data.index:
        raise ValueError(f"Ticker '{ticker}' not found.")
    return company_data.loc[ticker]['cik_str']



@tool
def get_company_facts_data(cik: str) -> dict:
    """
    Retrieves company facts data from the SEC using the given CIK.

    Args:
        cik (str): The CIK value of the company.

    Returns:
        dict: A dictionary containing the company facts data.
    """
    response = requests.get(
        f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
        headers={"User-Agent": "YourAppName"}
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch data for CIK {cik}.")
    return response.json()


@tool
def calculate_roe(company_facts: dict) -> float:
    """
    Computes the return on equity (ROE) from SEC company facts data.

    Args:
        company_facts (dict): The company facts data retrieved from the SEC.

    Returns:
        float: The calculated ROE, or 0 if data is insufficient.
    """
    try:
        net_income_data = company_facts['facts']['us-gaap']['NetIncomeLoss']['units']['USD']
        equity_data = company_facts['facts']['us-gaap']['StockholdersEquity']['units']['USD']

        def get_latest_data(form_type: str):
            """
            Fetches net income and equity values for the specified form type (e.g., '10-K', '10-Q').

            Args:
                form_type (str): The type of form to search for (e.g., '10-K', '10-Q').

            Returns:
                tuple: Net income and equity values if found; otherwise, (0, 0).
            """
            accn = None
            net_income = equity = 0

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