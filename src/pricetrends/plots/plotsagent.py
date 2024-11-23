import os
from plotstools import get_file_path, create_plots

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_cohere import ChatCohere
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

def create_plots_agent(verbose=True):
    cohere_api_key=os.getenv("COHERE_API_KEY")

    # Initialize Cohere LLM
    llm = ChatCohere(temperature=0)

    tools = [get_file_path, create_plots]

    prompt = ChatPromptTemplate([
        (
            "system",
            """
                You are an advanced financial analysis assistant specializing in generating visual representations of stock trends.
                
                Use the tools below:
                - get_file_path: To fetch the file path for the trend data for a specific ticker and trend. Optional pass window or span parameter if available.
                - combine_file_paths: To combine the file paths of multiple trends and tickers received from get_file_path tool into a list.
                - create_plots: To generate and save plots based on the list received from combine_file_paths tool.

                When answering:
                1. Use `get_file_path` to generate file paths for requested tickers and trends.
                2. Combine the file paths into a list and pass this list of paths to `create_plots` tool.
                3. Use `create_plots` to generate and save the plots.
                4. Return the file path where the plot was saved. Only return this file path intact as it is without any changes or additional information.
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
    agent = create_plots_agent()
    response = agent.invoke({
        "input": "Plot Closing Prices for Nvidia (NVDA) and Exponential Moving Average with span 5 for Tesla (TSLA)"
    })
    print(response)