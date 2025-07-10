from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState, END
from langchain_core.messages import AIMessage
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent
from langchain_mongodb.agent_toolkit.toolkit import MongoDBDatabaseToolkit
from langchain_mongodb.agent_toolkit.database import MongoDBDatabase
from langchain_openai import ChatOpenAI
import os
from langchain.agents import Tool
from tools.fulltext_tool import fulltext_query_tool
from dotenv import load_dotenv
load_dotenv()

# You can adjust temperature or other params here

OPENAI_LLM = ChatOpenAI(
    temperature=0,
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    streaming=True,
    verbose=True
)

class ChatbotAgent:
    agent_name = "chatbot_agent"

    @staticmethod
    async def chatbot(state: MessagesState, config: RunnableConfig) -> Command:
        # Use thread_id or user_id for Mongo context
        thread_id = config["configurable"].get("thread_id")
        application_id = config["configurable"].get("thread_id")

        # Connect to your MongoDB
        db = MongoDBDatabase.from_connection_string(
            os.getenv("MongoUrl"),
            database="soc_incidents"
        )

        # Build toolkit with your MongoDB connection and LLM
        toolkit = MongoDBDatabaseToolkit(db=db, llm=OPENAI_LLM)

        # Define the Mongo full-text search tool
        mongo_fulltext_tool = Tool.from_function(
            func=fulltext_query_tool,
            name="MongoFullTextSearch",
            description="""
        Use this tool to retrieve cybersecurity incidents from MongoDB using full-text semantic search.
        The incidents are stored in documents under the field "data". Example structure:

        Use this to perform full-text semantic search over incident fields like summary or recommendations.
        Input format (dict):
        {
          "collection": "Incident Report INCxxxxx",
          "query": "unauthorized login attempts or privilege escalation",
          "search_field": "summary" or "thread_type",
          "search_index_name": "default"
        }

        You must extract data from within the "data" field of each document.
        Use fields like 'summary', 'recommended_actions', or 'impact' to answer the user's query.
        Return a clean summary in structured bullet format.
        """
        )

        tools_box = toolkit.get_tools()
        # print(f"tools_box: {tools_box}")
        # tools_box.append(mongo_fulltext_tool)


        # Custom prompt for your own use-case
        chatbot_agent = create_react_agent(
            model=OPENAI_LLM,
            tools=tools_box,
            # tools=tools,
            prompt = f"""
You are a SOC Analyst AI assistant. You have access to threat intelligence and security event data from MongoDB.
You are tasked with answering questions using ONLY the relevant logs from the MongoDB database tied to thread ID `{thread_id}`.

You have access to a MongoDB Toolkit that allows you to:
- Retrieve the list of available collections in the database.
- Query documents from those collections using relevant fields and filters.

Instructions:
- Use only the tools provided in the MongoDB Toolkit to retrieve relevant data.
- Do not hallucinate collection names or simulate tool calls such as `getCollection(...)`.
- If a user's question cannot be answered based on available database content, respond with: "The data is not available in the logs."
- Keep your responses concise, factual, and aligned with the retrieved data.

MongoDB logs typically include fields such as: `timestamp`, `hostname`, `PID`, `level`, and `message`.

Your job:
- Carefully read and understand the user's question.
- Use the toolkit tools when necessary to explore the database.
- Provide a clear, evidence-based response based on the query results.
""".format(application_id=application_id)
        )

        # Invoke the chatbot logic
        result = await chatbot_agent.ainvoke(state)
        # LOGGER.debug(result)

        return Command(
            update={"messages": [AIMessage(content=result["messages"][-1].content, name=ChatbotAgent.agent_name)]},
            goto=END,
        )
