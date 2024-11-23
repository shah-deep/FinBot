from .trends.trendsagent import create_trends_agent
from .plots.plotsagent import create_plots_agent

from langchain.schema import BaseMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

trends_agent = create_trends_agent(verbose=True)
plot_agent = create_plots_agent(verbose=True)


class State(TypedDict):
    """
    Response from tool agents are stored in the State as a message dict
    """
    messages: dict


def get_message_content(state: State) -> str:
    last_message = state["messages"]
    if(isinstance(last_message, BaseMessage)):
        return last_message.content
    if(isinstance(last_message, dict)):
        return last_message['content']
        

def trends_node(state: State) -> State:
    content = get_message_content(state)
    response = trends_agent.invoke({"input": content})
    return {"messages": 
            {
                "sender": "trends_agent",
                "content": response["output"],
                "role": "human"
            }      
        }

def plots_node(state: State) -> State:
    content = get_message_content(state)
    response = plot_agent.invoke({"input": content})

    return {"messages": 
            {
                "sender": "plot_agent",
                "content": response["output"],
                "role": "human"
            }      
        }


def route_tools(state: State):
    last_message = state["messages"]
    if(isinstance(last_message, BaseMessage) and ('next' in last_message.additional_kwargs)):
        args = last_message.additional_kwargs
        if(args["sender"]=="trends_saver"):
            return "plots_maker"
        if(args["sender"]=="plots_maker"):
            return END

    return END
    

def prices_graph_builder():
    builder = StateGraph(State)
    builder.add_edge(START, "trends_saver")

    builder.add_node("trends_saver", trends_node)
    builder.add_node("plots_maker", plots_node)

    builder.add_edge("trends_saver", "plots_maker")
    builder.add_conditional_edges("plots_maker", route_tools)

    graph = builder.compile()

    return graph

