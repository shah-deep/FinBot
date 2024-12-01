from .trends.trendsagent import create_trends_agent
from .plots.plotsagent import create_plots_agent

from langchain.schema import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict


class PricesAgent:
    """
    The PricesAgent class orchestrates tasks between two tool agents: trends_agent and plot_agent.
    It facilitates identifying trends and generating plots for stock or financial data based on user input.
    """

    def __init__(self, verbose=False):
        self.trends_agent = create_trends_agent(verbose=verbose)
        self.plot_agent = create_plots_agent(verbose=verbose)

    class State(TypedDict):
        """
        Response from tool agents are stored in the State as a message dict
        """
        messages: dict


    def get_message_content(self, state: State) -> str:
        last_message = state["messages"]
        if(isinstance(last_message, BaseMessage)):
            return last_message.content
        if(isinstance(last_message, dict)):
            return last_message['content']
            

    def trends_node(self, state: State) -> State:
        """
        Performs data gathering using the trends_agent.
        """
        content = self.get_message_content(state)
        response = self.trends_agent.invoke({"input": content})
        return {"messages": 
                {
                    "sender": "trends_agent",
                    "content": response["output"],
                    "role": "human"
                }      
            }

    def plots_node(self, state: State) -> State:
        """
        Generate plots based on the analyzed trends using the plot_agent.
        """
        content = self.get_message_content(state)
        if(content=="Error"):
            response = "Error"
        else:
            response = self.plot_agent.invoke({"input": content})

        return {"messages": 
                {
                    "sender": "plot_agent",
                    "content": response["output"],
                    "role": "human"
                }      
            }


    def route_tools(self, state: State):
        last_message = state["messages"]
        if(isinstance(last_message, BaseMessage) and ('next' in last_message.additional_kwargs)):
            args = last_message.additional_kwargs
            if(args["sender"]=="trends_saver"):
                return "plots_maker"
            if(args["sender"]=="plots_maker"):
                return END

        return END
        

    def prices_graph_builder(self) -> CompiledGraph:
        builder = StateGraph(self.State)
        builder.add_edge(START, "trends_saver")

        builder.add_node("trends_saver", self.trends_node)
        builder.add_node("plots_maker", self.plots_node)

        builder.add_edge("trends_saver", "plots_maker")
        builder.add_conditional_edges("plots_maker", self.route_tools)

        graph = builder.compile()

        return graph

