import os
from .trendstools import (refresh_stock_data, check_stock_data, 
                        get_closing_price, get_moving_average, get_exponential_moving_average, get_short_moving_average, get_long_moving_average)
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_cohere import ChatCohere
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Dict

load_dotenv()

def create_trends_agent(verbose=False):
    cohere_api_key=os.getenv("COHERE_API_KEY")
    # Initialize Cohere LLM
    llm = ChatCohere(temperature=0)


    # Create the list of tools
    tools = [
        refresh_stock_data, 
        check_stock_data,                     
        get_closing_price, 
        get_moving_average, 
        get_exponential_moving_average, 
        get_short_moving_average, 
        get_long_moving_average
    ]

    prompt = ChatPromptTemplate([
        (
            "system",
            """
                You are a financial analysis assistant specializing in stock trend analysis using closing prices and moving averages.
                
                Use tool with name starting from get_ to fetch specific trend data and save it after checking company stock data.

                When answering:
                1. Check if company stock data is available for given ticker with check_stock_data tool.
                2. If it returns False, use refresh_stock_data tool to fetch company stock data.
                3. Select appropriate tool for getting specific trend data by passing company ticker.
                4. When all requested trends are fetched, return message telling to generate plot for given trends and tickers. This message will be used by another agent.
                5. If you get error at any step in the process, respond with single word "Error" and nothing else.
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
        handle_parsing_errors=False,
    )

    return agent_executor


if __name__ == "__main__":
    agent = create_trends_agent()
    response = agent.invoke({
        "input": "Retrieve Closing Prices for Nvidia (NVDA) and Exponential Moving Average with span 5 for Tesla (TSLA)"
    })
    print(response)