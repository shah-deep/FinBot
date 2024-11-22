import os
from pricetools import (refresh_stock_data, check_stock_data, 
                        get_closing_price, get_moving_average, get_exponential_moving_average, get_short_moving_average, get_long_moving_average)
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_cohere import ChatCohere
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Dict

load_dotenv()
cohere_api_key=os.getenv("COHERE_API_KEY")


# Initialize Cohere LLM
llm = ChatCohere(temperature=0)

class PriceDataResponse(BaseModel):
    """
    Response model for get closing price and get moving average. Use it for tool names starting with "get_". 
    Must use it for tool get_closing_price and  _moving_average tools.
    """
    ticker: str = Field(..., description="The stock ticker symbol for which the moving average was calculated.")
    info: str = Field(..., description="A description of the moving average calculation.")
    data: Dict[str, float] = Field(
        ..., 
        description="A dictionary mapping timestamps (in ISO format) to their corresponding moving average values."
    )


# Create the list of tools
tools = [
    refresh_stock_data, 
    check_stock_data,                     
    get_closing_price, 
    get_moving_average, 
    get_exponential_moving_average, 
    get_short_moving_average, 
    get_long_moving_average,
    # PriceDataResponse
]

# structured_llm = llm.with_structured_output(PriceDataResponse)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                You are a financial analysis assistant specializing in stock trend analysis using closing prices and moving averages.
                
                Use tool with name starting from get_ to fetch specific trend data after checking company stock data.

                When answering:
                1. Check if company stock data is available for given ticker with check_stock_data tool.
                2. If it returns False, use refresh_stock_data tool to fetch company stock data.
                3. Select appropriate tool for getting specific trend data by passing company ticker.
                4. Return the data as it is in JSON format.
            """, # 4. Apply PriceDataResponse tool to format the results and return it.
        ),
        # ("placeholder", "{history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# llm_withtool =  llm.bind_tools([PriceDataResponse])

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
    verbose=True,
    handle_parsing_errors=True,
)



response = agent_executor.invoke({
    "input": "Get for Closing Prices for Nvidia (NVDA)"
})
print(response)
# PriceDataResponse.model_validate()