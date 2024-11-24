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
techplot_agent = prices_graph_builder()


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
    print("Ratios Node Response: ", response)
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
    print("Techplot Node Response: ", response, " | type: ", type(response))
    
    if(isinstance(response, dict) and ("messages" in response)):
        output = response["messages"]["content"]
    elif(isinstance(response, str) and isinstance(eval(response), dict) and ("messages" in response)):
        output = response["messages"]["content"]
    else:
        output = f"Plot Failed, Retry: {content}"

    return {"messages": [
            {
                "sender": "techplot_agent",
                "content": output,
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
    You are a supervisor tasked with managing a conversation between the following {agent_name_var}s: ratios_agent and techplot_agent.

    Your responsibility is to decide which {agent_name_var} should act next, based on the user's request and the current state of the task.  
    Each {agent_name_var} will perform a task and provide results along with a status update.  

    Available {agent_name_var}s and their capabilities:
    - ratios_agent: {agent_utilities['ratios_agent']}
    - techplot_agent: {agent_utilities['techplot_agent']}

    Respond with one of the following options:
    "ratios_agent" | "techplot_agent"
    """
)


llm = ChatCohere(model="command-r-plus")

def supervisor_node(state: State) -> State:
    print("STATE Supervisor ", state)

    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.invoke(messages) # .with_structured_output(Router)
    # content_ = state["messages"]
    next_ = "supervisor"
    if(isinstance(response, BaseMessage)):
        next_ = response.content
        next_ = next_.lower()
        print(f"Got Next: {next_}")

    # print("Response:  ", response)    
    if(next_ not in ["ratios_agent", "techplot_agent"]):
        print(f"ERROR: WRONG OUTPUT FROM SUPERVISOR -- {response}")


    content_ = get_message_content(state)

    return {"messages": [
            {
                "sender": "supervisor",
                "next": next_,
                "content": content_,
                "role": "assistant", # Use one of 'human', 'user', 'ai', 'assistant', 'function', 'tool', or 'system'
            }      
        ]}


def route_tools(state: State):
    last_message = state["messages"][-1]
    print(last_message)
    if(isinstance(last_message, BaseMessage) and ('next' in last_message.additional_kwargs)):
        args = last_message.additional_kwargs
        return args["next"]
    print("Returned Supervisor")
    return END
    

def supervisor_graph_builder():
    builder = StateGraph(State)
    builder.add_edge(START, "supervisor")
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("ratios_agent", ratios_node)
    builder.add_node("techplot_agent", techplot_node)

    # Agents will always respond to the supervisor
    builder.add_edge("ratios_agent", END)
    builder.add_edge("techplot_agent", END)

    builder.add_conditional_edges("supervisor", route_tools)

    graph = builder.compile()

    return graph


class HelperAgent:
    def __init__(self, graph):
        self.graph = graph

    def send_message(self, user_input: str):
        response = self.graph.invoke({"messages": [HumanMessage(content=user_input)],})
        if (isinstance(response, dict) and ("messages" in response)):
            last_message = response["messages"][-1]
            if(isinstance(last_message, BaseMessage)):
                output = {
                    "sender": last_message.additional_kwargs["sender"],
                    "response": last_message.content
                }
                return output
            
        return f"Error with the agents. Got response: {response} |"
    
    def get_graph(self):
        return self.graph


def create_agent():
    graph = supervisor_graph_builder()
    agent = HelperAgent(graph)
    return agent
