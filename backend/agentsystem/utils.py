from langchain_core.messages import HumanMessage
from langchain.schema import BaseMessage
from .teams_supervisor import SupervisorAgent
from cohere.errors.too_many_requests_error import TooManyRequestsError


class HelperAgent:
    """
    A wrapper agent for interacting with a task execution graph. It facilitates communication 
    between the user and the agents within the graph.
    """

    def __init__(self, graph):
        self.graph = graph

    def send_message(self, user_input: str):
        """
        Sends a user input message to the graph and processes the response.
        """
        
        try:
            response = self.graph.invoke({"messages": [{"sender": "user", "content": user_input, "role": "human"}]})
            if (isinstance(response, dict) and ("messages" in response)):
                last_message = response["messages"][-1]
                if(isinstance(last_message, BaseMessage)):
                    return last_message.content
                
            if(isinstance(response, BaseMessage)): 
                return response.content
            
            raise ValueError(f"Incorrect format for agent response. Got response: {response}")
        
        except TooManyRequestsError:
            return "TooManyRequestsError"
        
        except Exception as e:
            print(f"Error in processing: {e}")
            return "Error"
            
    def get_graph(self):
        return self.graph


def create_agent(company_ticker: str):
    agent_maker = SupervisorAgent(company_ticker)
    graph = agent_maker.supervisor_graph_builder()
    agent = HelperAgent(graph)
    return agent
