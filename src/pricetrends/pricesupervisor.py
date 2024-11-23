from .trends.trendsagent import create_trends_agent
from .plots.plotsagent import create_plots_agent

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
    content = get_message_content(state)
    response = plot_agent.invoke({"input": content})
    print("Trends Node Response: ", response)
    return {"messages": [
            {
                "sender": "plot_agent",
                "content": response["output"],
                "role": "human"
            }      
        ]}

agent_name_var = "worker"
system_prompt = (
    f"""
    Returns:
        dict:
            next: str
            prompt: str

    You are a supervisor tasked with managing a conversation between the following {agent_name_var}s: trends_saver, plots_maker.
    
    You must always respond with two values, "next" and "prompt".
    "next" should be the {agent_name_var} to act next (trends_saver or plots_maker) or "FINISH" when all done.
    "prompt" should be the task this {agent_name_var} needs to perform. When all done, make a list of all image path received from plots_maker and return this list in "prompt".

    For your response, ALWAYS Make a key-value pair with keys "next" and "prompt" corresponding values.  Example:   {{"next":"trends_saver", "prompt":"Get closing price of TSLA and NVDA."}}
    Always Only return this key-value pair intact as it is without any changes or additional information.


    The user request will always be to plot some stock trends based on some company tickers.
    For every user request, identify what different comparisons does the user want.
    (Example: One plot for closing price of TSLA and NVDA, and another plot for short moving averages of AAPL and MSFT.)
    First clearly identifying the list of comparisons.
    
    Your task is ask {agent_name_var}s to act. Follow these steps for each comparison and ask {agent_name_var}s to act:
    1. Use trends_saver {agent_name_var} to get the required trends data and save it on server. For this, "next" is trends_saver and "prompt" is the task it needs to do. Return: {{"next":"trends_saver", "prompt":...}}
    2. Use plots_maker {agent_name_var} to generate a plot and get back the image path. For this, set "next" as plots_maker and "prompt" is the task it needs to do. Return: {{"next":"plots_maker", "prompt":...}}
    3. Repeat 1. and 2. if needed.
    4. When all done, "next" should be "FINISH". Make a list of all image path received from plots_maker and return this list in "prompt". Return: {{"next":"FINISH", "prompt": [...]}}

    Each {agent_name_var} will perform a task and respond with their status or results. 
    
    """ 
)

class Router(TypedDict):
    """
    Always structure response with this tool. 
    """
    next: Literal["FINISH", "trends_saver", "plots_maker"]
    prompt: str

llm = ChatCohere(model="command-r-plus", verbose=True)

def supervisor_node(state: State) -> State:
    print("STATE Supervisor ", state)
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.invoke(messages) # .with_structured_output(Router)
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
    builder.add_node("trends_saver", trends_node)
    builder.add_node("plots_maker", plots_node)

    # Agents will always respond to the supervisor
    builder.add_edge("trends_saver", "supervisor")
    builder.add_edge("plots_maker", "supervisor")

    # builder.add_edge("supervisor", END)

    builder.add_conditional_edges("supervisor", route_tools)

    graph = builder.compile()

    return graph

