from .trends.trendsagent import create_trends_agent
from .plots.plotsagent import create_plots_agent

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

trends_agent = create_trends_agent(verbose=True)
plot_agent = create_plots_agent(verbose=True)


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
        

def trends_node(state: State) -> State:
    content = get_message_content(state)
    response = trends_agent.invoke({"input": content})
    print("Trends Node Response: ", response)
    return {"messages": [
            {
                "sender": "trends_agent",
                "content": response["output"],
                "role": "human"
            }      
        ]}

def plots_node(state: State) -> State:
    print("Plots node state ", state)
    content = get_message_content(state)
    response = plot_agent.invoke({"input": content})
    print("Plots Node Response: ", response)
    return {"messages": [
            {
                "sender": "plot_agent",
                "content": response["output"],
                "role": "human"
            }      
        ]}


def route_tools(state: State):
    print(state)
    if (isinstance(state, dict) and ("messages" in state)):
        last_message = state["messages"][-1]
        if(isinstance(last_message, BaseMessage) and ('next' in last_message.additional_kwargs)):
            args = last_message.additional_kwargs
            if(args["sender"]=="trends_saver"):
                return "plots_maker"
            if(args["sender"]=="plots_maker"):
                return END
            print("ROUTE SENDER: ", args["sender"])

    return END
    

def prices_graph_builder():
    builder = StateGraph(State)
    builder.add_edge(START, "trends_saver")
    # builder.add_node("supervisor", supervisor_node)
    builder.add_node("trends_saver", trends_node)
    builder.add_node("plots_maker", plots_node)

    # Agents will always respond to the supervisor
    builder.add_edge("trends_saver", "plots_maker")
    # builder.add_edge("plots_maker", "supervisor")

    # builder.add_edge("plots_maker", END)

    builder.add_conditional_edges("plots_maker", route_tools)

    graph = builder.compile()

    return graph

