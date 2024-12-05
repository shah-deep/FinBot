from backend.agentsystem.financialratios.finratioagent import create_finratios_agent
from backend.agentsystem.pricetrends.pricesupervisor import PricesAgent

import json, os
import yfinance as yf
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.schema import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict, Literal, Annotated, List
from langchain_cohere import ChatCohere
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv(override=True)


class SupervisorAgent:
    """
    This class orchestrates tasks between different tool agents for managing company-related requests. 
    It handles agents for financial ratios, price trends, and company information, delegating tasks based on user input.
    """

    def __init__(self, company_ticker):  
        """
        Initialize the SupervisorAgent with a company ticker.
        """
        cohere_api_key=os.getenv("COHERE_API_KEY")
        # print(cohere_api_key)
        self.company_ticker = company_ticker.upper()
        self.tkr_msg = f"  Company Ticker is '{self.company_ticker}.'"
        self.ratios_agent = create_finratios_agent(verbose=False)
        self.techplot_agent = PricesAgent().prices_graph_builder()
        self.llm = ChatCohere(model="command-r-plus", temperature=0)
        self.structured_llm = self.llm.with_structured_output(self.AgentSelection)
        self.agent_calls = None

        try:
            self.company_info = yf.Ticker(company_ticker).info
        except:
            self.company_info = {"longName": "Unknown", "longBusinessSummary": "Unknown"}

        self.init_constants()

    class State(TypedDict):
        """
        Response from tool agents are added to the State messages list as a dict(sender: , **kwargs)
        """
        messages: Annotated[list[dict], add_messages]

    class AgentSelection(BaseModel):
        next: List[Literal["ratios_agent", "techplot_agent", "compinfo_agent"]] = Field(
            description="List of agents to call for this task"
        )
        prompt: List[str] = Field(description="List of tasks that these agents should perform")

    def get_message_content(self, state: State) -> str:
        if (isinstance(state, dict) and ("messages" in state)):
            last_message = state["messages"][-1]
            if(isinstance(last_message, BaseMessage)):
                return last_message.content
            

    def ratios_node(self, state: State) -> State:
        """
        Handles requests related to financial ratios.
        """

        content = self.get_message_content(state)
        content += self.tkr_msg
        response = self.ratios_agent.invoke({"input": content})
        print("Ratios Node Response: ", response)
        return {"messages": [
                {
                    "sender": "ratios_agent",
                    "content": response["output"],
                    "role": "tool",
                    "tool_call_id": "random",
                }      
            ]}

    def techplot_node(self, state: State) -> State:
        """
        Handles requests related to stock price trend analysis.
        """

        content = self.get_message_content(state)
        content += self.tkr_msg
        response = self.techplot_agent.invoke({"messages": HumanMessage(content=content), })
        print("Techplot Node Response: ", response)
        
        if(isinstance(response, dict) and ("messages" in response)):
            output = response["messages"]["content"]
        elif(isinstance(response, str) and isinstance(eval(response), dict) and ("messages" in eval(response))):
            output = eval(response)["messages"]["content"]
        else:
            output = f"Plot Failed, Retry: {content}"

        return {"messages": [
                {
                    "sender": "techplot_agent",
                    "content": output,
                    "role": "ai"
                }      
            ]}
    
    
    def compinfo_node(self, state: State) -> State:
        """
        Handles requests for general company information.
        """

        content = self.get_message_content(state)
        messages = [SystemMessage(content=self.infoagent_prompt), HumanMessage(content=content)]
        response = self.llm.invoke(messages)
        print("Company Info Node Response: ", response)

        output = "This information is not available."
        if(isinstance(response, BaseMessage)):
            output = response.content
            if(output.strip(" .'").strip('"').upper() == "ERROR"):
                output = "Error"

        return {"messages": [
                {
                    "sender": "compinfo_agent",
                    "content": output,
                    "role": "ai"
                }      
            ]}


    def init_constants(self):
        agent_name_var = "worker"

        agent_utilities = {
            "ratios_agent": ("getting performance, efficiency, and financial health of a company. It calculates company's financial metrics or financial ratios which include " 
                            "Profitability Metrics such as Return on Equity (ROE), Return on Assets (ROA), Net Profit Margin, Gross Margin, "
                            "and Leverage/Financial Stability Metrics such as Debt to Equity, Interest Coverage. "
                            ),
            "techplot_agent": ("perform stock trend analysis by comparing and plotting technical indicators such as moving averages. "
                            "Specifically, it can be used to compare or plot "
                            "closing prices, moving average for given window, short moving average, long moving average, exponential moving average for given span."
                            ),
            "compinfo_agent": "get company name, ticker or business summary"
        }

        self.system_prompt = (
            f"""
            You are a supervisor tasked with managing a conversation between the following {agent_name_var}s: ratios_agent, techplot_agent and compinfo_agent.

            Your responsibility is to decide which {agent_name_var} should act next, based on the user's request and the current state of the task.  
            Each {agent_name_var} will perform a task and provide results along with a status update.  

            Available {agent_name_var}s and their capabilities:
            - ratios_agent: {agent_utilities['ratios_agent']}
            - techplot_agent: {agent_utilities['techplot_agent']}
            - compinfo_agent: {agent_utilities['compinfo_agent']}
            - finish: If none of the previous {agent_name_var}s can do this task.

            "next" is list from the following options:
            "ratios_agent" | "techplot_agent" | "compinfo_agent" | "finish"

            "prompt": List of tasks these agents should perform. Based on user's request, create a new prompt for each "next" in the same order as {agent_name_var} in "next". 
            """
        )

        self.infoagent_prompt = (
            f"""
            You are a helper agent answering general questions about a company. 
            Only give answers related to this company. If you are unable to answer related to this company, say that it is not available. 
            If you get any errors, reply with a single word "ERROR".
            
            Company Name: {self.company_info["longName"]}  
            Company Stock Ticker: {self.company_ticker}  
            Company Business Summary: {self.company_info["longBusinessSummary"]}
        """)
       

    def supervisor_node(self, state: State) -> State:
        """
        Supervises and routes requests to the appropriate agent based on the current state.
        """
        
        last_sender = state["messages"][-1].additional_kwargs["sender"]
        # print(f"Supervisor got message from {last_sender}")
        
        if(last_sender=="user"):
            messages = [SystemMessage(content=self.system_prompt)] + state["messages"]
            response = self.structured_llm.invoke(messages)
            print(f"Supervisor Resonse: {response}")

            if(isinstance(response, self.AgentSelection)):
                if(not (isinstance(response.next, list) and isinstance(response.prompt, list))):
                    next_, content_ = END, response.content
                else:
                    self.agent_calls = list(zip(response.next, response.prompt))
                    self.results = []
            else:
                next_ = END
                self.results = "Error"
            
        else:  
            self.results.append({
                "sender": last_sender,
                "content": self.get_message_content(state)
            })

        if(not self.agent_calls):
            next_ = END
            content_ = self.results
            self.results = []
            self.agent_calls = None
        else:
            next_, content_ = self.agent_calls.pop(0)
            

        if(next_=="finish"):
            next_ = END

        # print(f"Supervisor node, next: {next_}") #, content: {content_}")

        return {"messages": [
                {
                    "sender": "supervisor",
                    "next": next_,
                    "content": content_,
                    "role": "assistant", # Use one of 'human', 'user', 'ai', 'assistant', 'function', 'tool', or 'system'
                }      
            ]}


    def route_tools(self, state: State):
        """
        Routes the task to the appropriate worker based on the last message.
        """

        last_message = state["messages"][-1]
        # print(last_message)
        if(isinstance(last_message, BaseMessage) and ('next' in last_message.additional_kwargs)):
            args = last_message.additional_kwargs
            return args["next"]
        # print("Returned Supervisor")
        return END
        

    def supervisor_graph_builder(self) -> CompiledGraph:
        """
        Builds and compiles the state graph for orchestrating tasks between agents.
        """

        builder = StateGraph(self.State)
        builder.add_edge(START, "supervisor")
        builder.add_node("supervisor", self.supervisor_node)
        builder.add_node("ratios_agent", self.ratios_node)
        builder.add_node("techplot_agent", self.techplot_node)
        builder.add_node("compinfo_agent", self.compinfo_node)

        # Agents will always respond to the supervisor
        builder.add_edge("ratios_agent", "supervisor")
        builder.add_edge("techplot_agent", "supervisor")
        builder.add_edge("compinfo_agent", "supervisor")

        builder.add_conditional_edges("supervisor", self.route_tools)

        graph = builder.compile()

        return graph
