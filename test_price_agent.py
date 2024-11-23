from langchain_core.messages import HumanMessage
from src.pricetrends.pricesupervisor import prices_graph_builder

graph = prices_graph_builder()
user_input = "Plot Closing Prices for Nvidia (NVDA)"

events = graph.stream(
    {
        "messages": 
            HumanMessage(
                content=user_input
            )
        ,
    },
    # Maximum number of steps to take in the graph
    {"recursion_limit": 150},
)
for s in events:
    print(s)
    print("----")