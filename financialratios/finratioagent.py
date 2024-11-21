import os
from finratiotools import (refresh_company_data, get_cik_from_ticker, get_company_facts_data, 
                                           calculate_roe)
from langchain import hub
from langchain.tools import StructuredTool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory 
from langchain_cohere.llms import Cohere
from langchain_cohere import ChatCohere
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from pydantic import Field
from typing import Dict, Any, Annotated, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage

load_dotenv()
cohere_api_key=os.getenv("COHERE_API_KEY")


# Initialize Cohere LLM
llm = ChatCohere(
    temperature=0
)

# refresh_company_data_tool = StructuredTool.from_function(
#     func=refresh_company_data,
#     name="Refresh Company Data",
#     description="Refreshes the company ticker and CIK data.",
#     return_direct=False
# )

# get_cik_tool = StructuredTool.from_function(
#     func=get_cik_from_ticker,
#     name="Fetch CIK from Ticker",
#     description="Fetches the Central Index Key (CIK) value for a company using its ticker symbol.",
#     args_schema={
#         "ticker": Annotated[str, "The ticker symbol of the company"]
#     },
#     return_direct=False
# )

# get_company_facts_tool = StructuredTool.from_function(
#     func=get_company_facts_data,
#     name="Fetch Company Facts by CIK",
#     description="Fetches company facts data using its CIK value.",
#     args_schema={
#         "cik": Annotated[str, "The CIK value of the company"]
#     },
#     return_direct=False
# )

# calculate_roe_tool = StructuredTool.from_function(
#     func=calculate_roe,
#     name="Calculate ROE from Company Facts",
#     description="Calculates the return on equity (ROE) using company facts data.",
#     args_schema={
#         "company_facts": Annotated[Dict, "The company facts data from SEC"]
#     },
#     return_direct=False
# )

# Create the list of tools
tools = [
    refresh_company_data,
    get_cik_from_ticker,
    get_company_facts_data,
    calculate_roe
]

# Create a custom memory class to store company facts
class CompanyFactsMemory(ConversationBufferMemory):
    company_facts: Dict = Field(default_factory=dict)
    
    def __init__(self, **kwargs):
        super().__init__(return_messages=True)
        self.company_facts = {}
    
    def save_company_facts(self, cik: str, facts: dict):
        self.company_facts[cik] = facts
    
    def get_company_facts(self, cik: str) -> Optional[dict]:
        return self.company_facts.get(cik)
    
    def load_memory_variables(self, inputs: Dict) -> Dict:
        memory_data = super().load_memory_variables(inputs)
        memory_data["company_facts"] = self.company_facts
        return memory_data

class CompanyFactsCallbackHandler(BaseCallbackHandler):
    def __init__(self, memory: CompanyFactsMemory):
        self.memory = memory

    def on_tool_end(self, output: str, tool: str, tool_input: str, **kwargs: Any) -> None:
        if tool == "Fetch Company Facts by CIK":
            try:
                # Handle potential JSON string vs dict
                facts = output if isinstance(output, dict) else eval(output)
                self.memory.save_company_facts(tool_input, facts)
            except:
                pass

# Initialize memory
memory = CompanyFactsMemory()

# Create a custom prompt template that includes context about stored company facts
prompt_template = """You are a financial analysis assistant with access to SEC company data.
You have access to the following tools:

{tools}

When analyzing companies, remember to:
1. Refresh company data only if not available
2. Get CIK from ticker if ticker is provided
3. Using CIK, fetch company facts
4. Fetch company facts before performing calculations
5. Store company facts in memory for future use
6. Using company facts, perform calculations

Previous company facts stored in memory: {memory}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}

If the CIK and company facts are already available in memory, do not fetch them again. 
You can directly calculate the ROE. If the CIK and company facts are not available, fetch them first.

Thought: {agent_scratchpad}"""

prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["input", "tools", "tool_names", "agent_scratchpad", "memory"]
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
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
    callbacks=[CompanyFactsCallbackHandler(memory)]
)


# response = agent_executor.invoke({"input": "What is the ROE for Apple (AAPL)?"})
response = agent_executor.invoke({
    "input": "What is the ROE for Apple (AAPL)?",
    "tools": tools,
    "tool_names": [tool.name for tool in tools],  # Tool names extracted from the tools list
    "memory": memory.load_memory_variables({}),  # Ensure the memory data is included
})
print(response)