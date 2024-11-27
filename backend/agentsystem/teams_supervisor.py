from .financialratios.finratioagent import create_finratios_agent
from .pricetrends.pricesupervisor import PricesAgent

import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.schema import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledGraph
from typing import Literal, Annotated
from typing_extensions import TypedDict
from langchain_cohere import ChatCohere

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class SupervisorAgent:

    def __init__(self, company_ticker):   
        self.company_ticker = company_ticker 
        self.tkr_msg = f"  Company Ticker is '{self.company_ticker}.'"
        self.ratios_agent = create_finratios_agent(verbose=False)
        self.techplot_agent = PricesAgent().prices_graph_builder()
        self.llm = ChatCohere(model="command-r-plus")
        self.init_constants()

    class State(TypedDict):
        """
        Response from tool agents are added to the State messages list as a dict(sender: , **kwargs)
        """
        messages: Annotated[list[dict], add_messages]

    def get_message_content(self, state: State) -> str:
        if (isinstance(state, dict) and ("messages" in state)):
            last_message = state["messages"][-1]
            if(isinstance(last_message, BaseMessage)):
                return last_message.content
            

    def ratios_node(self, state: State) -> State:
        content = self.get_message_content(state)
        content += self.tkr_msg
        response = self.ratios_agent.invoke({"input": content})
        print("Ratios Node Response: ", response)
        return {"messages": [
                {
                    "sender": "ratios_agent",
                    "content": response["output"],
                    "role": "human"
                }      
            ]}

    def techplot_node(self, state: State) -> State:
        content = self.get_message_content(state)
        content += self.tkr_msg
        response = self.techplot_agent.invoke({"messages": HumanMessage(content=content), })
        print("Techplot Node Response: ", response)
        
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

    def init_constants(self):

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

        self.system_prompt = (
            f"""
            You are a supervisor tasked with managing a conversation between the following {agent_name_var}s: ratios_agent and techplot_agent.

            Your responsibility is to decide which {agent_name_var} should act next, based on the user's request and the current state of the task.  
            Each {agent_name_var} will perform a task and provide results along with a status update.  

            Available {agent_name_var}s and their capabilities:
            - ratios_agent: {agent_utilities['ratios_agent']}
            - techplot_agent: {agent_utilities['techplot_agent']}
            - finish: If none of the previous {agent_name_var}s can do this task.

            Respond with one of the following options:
            "ratios_agent" | "techplot_agent" | "finish"
            """
        )
        #  Check if both are true: a company's ticker is provided in the user input and the request is related to financial metrics or trends analysis. If not, respond with "finish". 



    def supervisor_node(self, state: State) -> State:
        # print("STATE Supervisor ", state)

        messages = [SystemMessage(content=self.system_prompt)] + state["messages"]
        response = self.llm.invoke(messages) # .with_structured_output(Router)
        # content_ = state["messages"]
        next_ = "supervisor"
        if(isinstance(response, BaseMessage)):
            next_ = response.content
            next_ = next_.lower()
            # print(f"Got Next: {next_}")

        # print("Response:  ", response)    
        if(next_ not in ["ratios_agent", "techplot_agent", "finish"]):
            print(f"ERROR: WRONG OUTPUT FROM SUPERVISOR -- {response}")

        if(next_=="finish"):
            next_ = END
            content_ = "Error"
        else:
            content_ = self.get_message_content(state)

        return {"messages": [
                {
                    "sender": "supervisor",
                    "next": next_,
                    "content": content_,
                    "role": "assistant", # Use one of 'human', 'user', 'ai', 'assistant', 'function', 'tool', or 'system'
                }      
            ]}


    def route_tools(self, state: State):
        last_message = state["messages"][-1]
        # print(last_message)
        if(isinstance(last_message, BaseMessage) and ('next' in last_message.additional_kwargs)):
            args = last_message.additional_kwargs
            return args["next"]
        # print("Returned Supervisor")
        return END
        

    def supervisor_graph_builder(self) -> CompiledGraph:
        builder = StateGraph(self.State)
        builder.add_edge(START, "supervisor")
        builder.add_node("supervisor", self.supervisor_node)
        builder.add_node("ratios_agent", self.ratios_node)
        builder.add_node("techplot_agent", self.techplot_node)

        # Agents will always respond to the supervisor
        builder.add_edge("ratios_agent", END)
        builder.add_edge("techplot_agent", END)

        builder.add_conditional_edges("supervisor", self.route_tools)

        graph = builder.compile()

        return graph
