import os


from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_cohere import ChatCohere
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv