from langchain_core.messages import HumanMessage
from src.pricetrends.pricesupervisor import prices_graph_builder

graph = prices_graph_builder()
user_input = "Plot Closing Prices for Nvidia (NVDA)"

response = graph.invoke({"messages": HumanMessage(content=user_input), })
print(response)