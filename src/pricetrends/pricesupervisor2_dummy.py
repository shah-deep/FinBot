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
    
    You must ALWAYS respond with exactly two key-value pairs, "next" and "prompt".
    - "next" specifies which {agent_name_var} acts next ("trends_saver", "plots_maker", or "FINISH").
    - "prompt" specifies the task that {agent_name_var} must perform.

    STRICT FORMAT:
    Always return a JSON object like this: {{"next": "agent_name", "prompt": "task_description"}}
    NEVER include any other information or explanation.

    EXAMPLES:
    1. {{"next": "trends_saver", "prompt": "Get closing price of TSLA and NVDA."}}
    2. {{"next": "plots_maker", "prompt": "Generate a plot for closing price of TSLA and NVDA."}}
    3. {{"next": "FINISH", "prompt": ["path_to_image1", "path_to_image2"]}}

    Instructions:
    1. For every user request, identify the list of comparisons the user wants.
    2. Sequentially:
        - Use trends_saver to get trends data. Example: {{"next": "trends_saver", "prompt": "Get closing price of TSLA and NVDA."}}
        - Use plots_maker to generate the plot. Example: {{"next": "plots_maker", "prompt": "Generate a plot comparing TSLA and NVDA trends."}}
    3. When all tasks are done, finalize with "FINISH" and a list of all image paths received. Example: {{"next": "FINISH", "prompt": ["image1.png", "image2.png"]}}

    DO NOT deviate from this format. DO NOT include any additional explanations or information.
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

