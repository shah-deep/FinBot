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
cik_last_fetch_time = time.time()
company_cik_data = fetch_company_data()
company_facts_data = {}


def refresh_company_cik_data():
    """
    Refreshes the global company data from the SEC API.
    """
    global company_cik_data
    company_cik_data = fetch_company_data()


@tool
def get_cik_from_ticker(ticker: str) -> str:
    """
    Retrieves the CIK value for a given company ticker.

    Args:
        ticker (str): The ticker symbol of the company.

    Returns:
        str: The CIK value associated with the ticker.
    """
    # global cik_last_fetch_time
    # if ((time.time()-cik_last_fetch_time) > 86400):
    #     cik_last_fetch_time = time.time()
    #     refresh_company_cik_data()

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


def get_latest_data(numerator, denominator, form_type):
    accn = None
    term1, term2 = 0, 0

    for report in reversed(numerator):
        if report['form'] == form_type:
            accn = report['accn']
            term1 = report['val']
            break

    if accn:
        for report in reversed(denominator):
            if report['accn'] == accn:
                term2 = report['val']
                break

    return term1, term2


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
    
    try:
        net_income_data = company_facts_data[cik]['data']['facts']['us-gaap']['NetIncomeLoss']['units']['USD']
        equity_data = company_facts_data[cik]['data']['facts']['us-gaap']['StockholdersEquity']['units']['USD']

        # Prioritize '10-K' and fallback to '10-Q' if needed
        net_income, equity = get_latest_data(net_income_data, equity_data, '10-K')
        if not (net_income and equity):
            net_income, equity = get_latest_data(net_income_data, equity_data, '10-Q')

        
        if net_income and equity:
            return net_income / equity
        
        return 0

    except KeyError as e:
        raise ValueError(f"Missing data in company facts: {e}")
    


@tool
def calculate_roa(cik: str) -> float:
    """
    Computes the Return on Assets (ROA) from SEC company facts data.
    It has global access to Company Facts Data.

    Args:
        cik (str): The CIK value of the company.

    Returns:
        float: The calculated ROA, or 0 if data is insufficient.
    """
    
    try:
        net_income_data = company_facts_data[cik]['data']['facts']['us-gaap']['NetIncomeLoss']['units']['USD']
        assets_data = company_facts_data[cik]['data']['facts']['us-gaap']['Assets']['units']['USD']

        # Prioritize '10-K' and fallback to '10-Q' if needed
        net_income, assets = get_latest_data(net_income_data, assets_data, '10-K')
        if not (net_income and assets):
            net_income, assets = get_latest_data(net_income_data, assets_data, '10-Q')

        
        if net_income and assets:
            return net_income / assets
        
        return 0

    except KeyError as e:
        raise ValueError(f"Missing data in company facts: {e}")
    


@tool
def calculate_net_profit_margin(cik: str) -> float:
    """
    Computes the Net Profit Margin from SEC company facts data.
    It has global access to Company Facts Data.

    Args:
        cik (str): The CIK value of the company.

    Returns:
        float: The calculated Net Profit Margin, or 0 if data is insufficient.
    """
    
    try:
        net_income_data = company_facts_data[cik]['data']['facts']['us-gaap']['NetIncomeLoss']['units']['USD']
        revenues_data = company_facts_data[cik]['data']['facts']['us-gaap']['Revenues']['units']['USD']

        # Prioritize '10-K' and fallback to '10-Q' if needed
        net_income, revenue = get_latest_data(net_income_data, revenues_data, '10-K')
        if not (net_income and revenue):
            net_income, revenue = get_latest_data(net_income_data, revenues_data, '10-Q')

        
        if net_income and revenue:
            return net_income / revenue
        
        return 0

    except KeyError as e:
        raise ValueError(f"Missing data in company facts: {e}")
    


@tool
def calculate_gross_margin(cik: str) -> float:
    """
    Computes the Gross Margin from SEC company facts data.
    It has global access to Company Facts Data.

    Args:
        cik (str): The CIK value of the company.

    Returns:
        float: The calculated Gross Margin, or 0 if data is insufficient.
    """
    
    try:
        gross_profit_data = company_facts_data[cik]['data']['facts']['us-gaap']['GrossProfit']['units']['USD']
        revenues_data = company_facts_data[cik]['data']['facts']['us-gaap']['Revenues']['units']['USD']

        # Prioritize '10-K' and fallback to '10-Q' if needed
        gross_profit, revenue = get_latest_data(gross_profit_data, revenues_data, '10-K')
        if not (gross_profit and revenue):
            gross_profit, revenue = get_latest_data(gross_profit_data, revenues_data, '10-Q')

        
        if gross_profit and revenue:
            return gross_profit / revenue
        
        # print(f"Gross margin for CIK: {cik}. GP:  {gross_profit} | R: {revenue}")
        return 0

    except KeyError as e:
        raise ValueError(f"Missing data in company facts: {e}")
    

@tool
def calculate_debt_equity(cik: str) -> float:
    """
    Computes the Debt to Equity from SEC company facts data.
    It has global access to Company Facts Data.

    Args:
        cik (str): The CIK value of the company.

    Returns:
        float: The calculated Debt to Equity Ratio, or 0 if data is insufficient.
    """
    
    try:
        liabilities_data = company_facts_data[cik]['data']['facts']['us-gaap']['Liabilities']['units']['USD']
        equity_data = company_facts_data[cik]['data']['facts']['us-gaap']['StockholdersEquity']['units']['USD']

        # Prioritize '10-K' and fallback to '10-Q' if needed
        liabilities, equity = get_latest_data(liabilities_data, equity_data, '10-K')
        if not (liabilities and equity):
            liabilities, equity = get_latest_data(liabilities_data, equity_data, '10-Q')

        
        if liabilities and equity:
            return liabilities / equity
        
        return 0

    except KeyError as e:
        raise ValueError(f"Missing data in company facts: {e}")



@tool
def calculate_interest_coverage(cik: str) -> float:
    """
    Computes the Interest Coverage from SEC company facts data.
    It has global access to Company Facts Data.

    Args:
        cik (str): The CIK value of the company.

    Returns:
        float: The calculated Interest Coverage Ratio, or 0 if data is insufficient.
    """
    
    try:
        operating_income_data = company_facts_data[cik]['data']['facts']['us-gaap']['OperatingIncomeLoss']['units']['USD']
        interest_expense_data = company_facts_data[cik]['data']['facts']['us-gaap']['InterestExpense']['units']['USD']

        # Prioritize '10-K' and fallback to '10-Q' if needed
        operating_income, interest_expense = get_latest_data(operating_income_data, interest_expense_data, '10-K')
        if not (operating_income and interest_expense):
            operating_income, interest_expense = get_latest_data(operating_income_data, interest_expense_data, '10-Q')

        
        if operating_income and interest_expense:
            return operating_income / interest_expense
        
        # print(f"interest_coverage for CIK: {cik}. OI:  {operating_income} | IE: {interest_expense}")
        return 0

    except KeyError as e:
        raise ValueError(f"Missing data in company facts: {e}")