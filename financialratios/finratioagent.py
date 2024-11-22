import os
from finratiotools import (refresh_company_cik_data, get_cik_from_ticker, check_company_facts_data, refresh_company_facts_data, calculate_roe)
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_cohere import ChatCohere
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any, Annotated, Optional
from dotenv import load_dotenv

load_dotenv()
cohere_api_key=os.getenv("COHERE_API_KEY")


# Initialize Cohere LLM
llm = ChatCohere(
    temperature=0
)

# Create the list of tools
tools = [
    # refresh_company_data,
    get_cik_from_ticker,
    refresh_company_facts_data,
    check_company_facts_data,
    calculate_roe
]


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                You are a financial analysis assistant with access to SEC company data. 
                
                Use calculate_roe tool to compute ROE after getting company facts data.

                When answering:
                1. Get CIK from ticker using get_cik_from_ticker tool.
                2. Using CIK, check if company facts data is available with check_company_facts_data tool.
                3. If it returns False, use refresh_company_facts_data to fetch company facts data.
                3. Select appropriate tool for performing calculations.
                4. Return the results as requested in the question.
            """,
        ),
        # ("placeholder", "{history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


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
    "input": "What is the ROE for Nvidia (NVDA) and Apple (AAPL)?"
})
print(response)