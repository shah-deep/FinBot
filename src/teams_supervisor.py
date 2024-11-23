from .financialratios.finratioagent import create_finratios_agent
from .pricetrends.pricesupervisor import prices_graph_builder

import json
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage
from langchain.schema import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from typing import Literal, Annotated
from typing_extensions import TypedDict
from langchain.prompts import ChatPromptTemplate
from langchain_cohere import ChatCohere

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


ratios_agent = create_finratios_agent(verbose=True)
techplot_agent = prices_graph_builder(verbose=True)


class State(TypedDict):
    """
    Response from tool agents are added to the State messages list as a dict(sender: , **kwargs)
    """
    messages: Annotated[list[dict], add_messages]


def get_message_content(state: State) -> str:
    if (isinstance(state, dict) and ("messages" in state)):
        last_message = state["messages"][-1]
        if(isinstance(last_message, BaseMessage)):
            return last_message.content
        

def ratios_node(state: State) -> State:
    content = get_message_content(state)
    response = ratios_agent.invoke({"input": content})
    print("Trends Node Response: ", response)
    return {"messages": [
            {
                "sender": "ratios_agent",
                "content": response["output"],
                "role": "human"
            }      
        ]}

def techplot_node(state: State) -> State:
    content = get_message_content(state)
    response = techplot_agent.invoke({"messages": HumanMessage(content=content), })
    print("Trends Node Response: ", response)
    return {"messages": [
            {
                "sender": "techplot_agent",
                "content": response["output"],
                "role": "human"
            }      
        ]}

agent_name_var = "worker"

agent_utilities = {
    "ratios_agent": ("calculate company's financial metrics or financial ratios which include " 
                      "Profitability Metrics such as Return on Equity (ROE), Return on Assets (ROA), Net Profit Margin, Gross Margin, "
                      "and Leverage/Financial Stability Metrics such as Debt to Equity, Interest Coverage. "
                      "These metrics are commonly used in analyzing the performance, efficiency, and financial health of a company."
                      ),
    "techplot_agent": ("perform stock trend analysis by comparing and plotting technical indicators such as moving averages. "
                       "Specifically, it can be used to compare or plot "
                       "closing prices, moving average for given window, short moving average, long moving average, exponential moving average for given span."
                       )
}

system_prompt = (
    f"""
    Returns: str

    You are a supervisor tasked with managing a conversation between the following {agent_name_var}s: ratios_agent, techplot_agent.  
    Given the following user request, respond with the worker to act next. Each worker will perform a task and respond with their results and status.  
    When finished, respond with FINISH.

    Available {agent_name_var}s are:
    ratios_agent: This {agent_name_var} can {agent_utilities['ratios_agent']}
    techplot_agent: This {agent_name_var} can {agent_utilities['techplot_agent']}
    """ 
)


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal["FINISH", "ratios_agent", "techplot_agent"]

llm = ChatCohere(model="command-r-plus", verbose=True)

def supervisor_node(state: State) -> State:
    print("STATE Supervisor ", state)

    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages) # .with_structured_output(Router)
    content_ = state["messages"]
    print("Response Content  ", response.content)
    next_ = "supervisor"
    
    if(response.content[0]=='{'):
        ai_msg = eval(response.content)
        
        if isinstance(ai_msg, dict):
            next_ = ai_msg["next"]
            content_ = ai_msg["prompt"]
            print(f"Got Next: {next_}")
    
    if(next_ == "supervisor"):
        print("ERROR in sup node")

    if next_ == "FINISH":
        next_ = END

    return {"messages": [
            {
                "sender": "supervisor",
                "next": next_,
                "content": content_,
                "role": "assistant", # Use one of 'human', 'user', 'ai', 'assistant', 'function', 'tool', or 'system'
            }      
        ]}

def route_tools(state: State):
    print(state)
    if (isinstance(state, dict) and ("messages" in state)):
        last_message = state["messages"][-1]
        if(isinstance(last_message, BaseMessage) and ('next' in last_message.additional_kwargs)):
            args = last_message.additional_kwargs
            if(args["sender"]=="supervisor"):
                return args["next"]
    print("Returned Supervisor")
    return "supervisor"
    

def prices_graph_builder():
    builder = StateGraph(State)
    builder.add_edge(START, "supervisor")
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("ratios_agent", ratios_node)
    builder.add_node("techplot_agent", techplot_node)

    # Agents will always respond to the supervisor
    builder.add_edge("ratios_agent", "supervisor")
    builder.add_edge("techplot_agent", "supervisor")

    # builder.add_edge("supervisor", END)

    builder.add_conditional_edges("supervisor", route_tools)

    graph = builder.compile()

    return graph

