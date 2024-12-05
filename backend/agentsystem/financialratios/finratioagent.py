import os
from backend.agentsystem.financialratios.finratiotools import (get_cik_from_ticker, check_company_facts_data, refresh_company_facts_data, 
                           calculate_roe, calculate_roa, calculate_net_profit_margin, calculate_gross_margin, calculate_debt_equity, calculate_interest_coverage)
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_cohere import ChatCohere
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

def create_finratios_agent(verbose=False):
    cohere_api_key=os.getenv("COHERE_API_KEY")

    # Initialize Cohere LLM
    llm = ChatCohere(
        temperature=0
    )

    # Create the list of tools
    tools = [
        get_cik_from_ticker,
        refresh_company_facts_data,
        check_company_facts_data,
        calculate_roe, 
        calculate_roa, 
        calculate_net_profit_margin, 
        calculate_gross_margin, 
        calculate_debt_equity, 
        calculate_interest_coverage
    ]


    prompt = ChatPromptTemplate([
        (
            "system",
            """
                You are a financial analysis assistant with access to SEC company data. 
                
                Use tool with name starting from calculate_ to compute value after checking company facts data.

                When answering:
                1. Get CIK from ticker using get_cik_from_ticker tool.
                2. Using CIK, check if company facts data is available with check_company_facts_data tool.
                3. If it returns False, use refresh_company_facts_data to fetch company facts data.
                4. Select appropriate tool for performing calculations. Consider zero (0) values as Data Not Available. If necessary tool is not given, you cannot complete the request.  
                5. Only if specifically asked for the performance, efficiency, or financial health, provide short summary as per the request.
                6. Return the results to the user as requested in the question.
            """,
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])


    # Create the agent
    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    # Create the agent executor with memory
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        handle_parsing_errors=True,
    )

    return agent_executor


if __name__ == "__main__":
    agent = create_finratios_agent()
    response = agent.invoke({
        "input": "What is the Net Profit Margin, Gross Margin, and Interest Coverage for Nvidia (NVDA) and Apple (AAPL)?"
    })
    print(response)