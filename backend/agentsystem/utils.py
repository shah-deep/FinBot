from langchain_core.messages import HumanMessage
from langchain.schema import BaseMessage
from .teams_supervisor import SupervisorAgent


class HelperAgent:
    def __init__(self, graph):
        self.graph = graph

    def send_message(self, user_input: str):
        try:
            response = self.graph.invoke({"messages": [HumanMessage(content=user_input)],})
            if (isinstance(response, dict) and ("messages" in response)):
                last_message = response["messages"][-1]
                if(isinstance(last_message, BaseMessage)):
                    output = {
                        "sender": last_message.additional_kwargs["sender"],
                        "response": last_message.content
                    }
                    return output
                
            if(isinstance(response, BaseMessage)):
                output = {
                    "sender": response.additional_kwargs["sender"],
                    "response": response.content
                }
                return output
            
            raise ValueError(f"Incorrect format for agent response. Got response: {response}")
        
        except Exception as e:
            print(f"Error in processing: {e}")
            output = {
                "sender": "system",
                "response": "Error"
            }
            return output
            
    def get_graph(self):
        return self.graph


def create_agent(company_ticker: str):
    agent_maker = SupervisorAgent(company_ticker)
    graph = agent_maker.supervisor_graph_builder()
    agent = HelperAgent(graph)
    return agent
