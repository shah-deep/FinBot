from trends.trendsagent import create_trends_agent
from plots.plotsagent import create_plots_agent

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from typing import Literal, Annotated
from typing_extensions import TypedDict
from langchain.prompts import ChatPromptTemplate
from langchain_cohere import ChatCohere

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

trends_agent = create_trends_agent()
plot_agent = create_plots_agent()


class State(TypedDict):
    """
    Response from tool agents are added to the State messages list as a dict(sender: , **kwargs)
    """
    messages: Annotated[list[dict], add_messages]

def trends_node(state: State) -> State:
    prompt_input = state["messages"][-1]["output"]
    response = trends_agent.invoke(prompt_input)
    return {"messages": [
            {
                "sender": "trends_agent",
                "output": response["output"]
            }      
        ]}

def plots_node(state: State) -> State:
    prompt_input = state["messages"][-1]["output"]
    prompt_input = prompt_input
    response = trends_agent.invoke(prompt_input)
    return {"messages": [
            {
                "sender": "plots_agent",
                "output": response["output"]
            }      
        ]}


system_prompt = (
    """
    You are a supervisor tasked with managing a conversation between the following agents: trends_saver, plots_maker.
    
    The user request will always be to plot some stock trends based on some company tickers.
    For every user request, identify what different comparisons does the user want.
    (Example: One plot for closing price of TSLA and NVDA, and another plot for short moving averages of AAPL and MSFT.)
    First clearly identifying the list of comparisons.
    
    Your task is ask agents to act. Follow these steps for each comparison and ask agents to act:
    1. Use trends_saver agent to get the required trends data and save it on server.
    2. Use plots_maker agent to generate a plot and get back the image path.

    Each agent will perform a task and respond with their status or results. 
    
    You must always respond with two values, "next" and "prompt".
    "next" should be the agent to act next (trends_saver or plots_maker) or "FINISH" when all done.
    "prompt" should be the task this agent needs to perform. When all done, make a list of all image path received from plots_maker and return this list in "prompt".
    """ 
)

class Router(TypedDict):
    """
    Agent to route to next. If no workers needed, route to FINISH.
    Prompt for the agent given.
    """
    next: Literal["FINISH", "trends_saver", "plots_maker"]
    prompt: str

llm = ChatCohere(model="command-r-plus")

def supervisor_node(state: State) -> State:
    messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    next_ = response["next"]
    if next_ == "FINISH":
        next_ = END

    return {"messages": [
            {
                "sender": "supervisor",
                "next": next_,
                "prompt": response["prompt"]
            }      
        ]}
    
    
def graph_builder():
    builder = StateGraph(State)
    builder.add_edge(START, "supervisor")
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("trends_saver", trends_node)
    builder.add_node("plots_maker", plots_node)

    # Agents will always respond to the supervisor
    builder.add_edge("trends_saver", "supervisor")
    builder.add_edge("plots_maker", "supervisor")

    # builder.add_edge("supervisor", END)

    builder.add_conditional_edges("supervisor", lambda state: state["next"])

    graph = builder.compile()

    return graph




