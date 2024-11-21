import requests
import pandas as pd
from langchain.tools import tool

headers = {'User-Agent': "ds@email.com"}

@tool
def roe(
    net_income: float,
    equity: float,
) -> float:
    """
    Computes the return on equity (ROE) for a given company.
    Use this function to evaluate the profitability of a company.
    """
    return net_income / equity

def get_company_data():
    company_tickers = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=headers
        )

    company_data = pd.DataFrame.from_dict(company_tickers.json(), orient='index')

    company_data['cik_str'] = company_data['cik_str'].astype(str).str.zfill(10) # add leading zeros to CIK
    company_data = company_data.set_index('ticker')
    return company_data

company_data = get_company_data()

@tool(
        name="Cik value from Ticker", 
        description="Fetches cik value for a company from its ticker.")
def get_cik_from_ticker(ticker: str) -> str:
    """
    Use this tool to get CIK for a company when its ticker is given.
    """
    cik = company_data.loc[ticker]['cik_str']
    return cik


@tool(
    name="Company Facts Data from Cik value", 
    description="Fetches company facts data from its cik value.")
def get_company_facts_data(cik: str):
    """
    Use this tool to get company facts data when its cik value is given.
    """
    company_facts = requests.get(
            f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
            headers=headers
        ).json()
    return company_facts


@tool(
    name="ROE from Company Facts Data", 
    description="Calculates return on equity (ROE) when Company Facts Data is given.")
def calculate_roe(company_facts) -> float:
    """
    Computes the return on equity (ROE) for a given company when Company Facts Data is given.
    Use this function to evaluate the profitability of a company.
    """
    netincomeloss = company_facts['facts']['us-gaap']['NetIncomeLoss']['units']['USD']

    def get_income_equity(form):
        accn, net_income_loss, stockholders_equity = None, 0, 0

        for report in netincomeloss[::-1]:
            if(report['form'] == form):
                accn=report['accn']
                net_income_loss=report['val']
                break
        if(accn):
            for report in company_facts['facts']['us-gaap']['StockholdersEquity']['units']['USD'][::-1]:
                if(report['accn']==accn):
                    stockholders_equity=report['val']
                    break
        
        return net_income_loss, stockholders_equity

    def get_income_equity_recur():
        net_income_loss, stockholders_equity = get_income_equity('10-K')
        if not (net_income_loss and stockholders_equity):
            net_income_loss, stockholders_equity = get_income_equity('10-Q')

        return net_income_loss, stockholders_equity
    
    net_income, equity = get_income_equity_recur()

    if(net_income and equity):
        return net_income/equity
    else:
        return 0