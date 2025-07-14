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
from langchain_mongodb.agent_toolkit import MONGODB_AGENT_SYSTEM_PROMPT
from dotenv import load_dotenv
load_dotenv()

# Tools
from tools.fulltext_tool import fulltext_query_tool
from tools.vector_search_tool import vector_search_across_collections
from tools.collection_list_tool import get_collection_names

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
        id = config["configurable"].get("thread_id")

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

        mongo_collection_list_tool = Tool.from_function(
                func=get_collection_names,
                name="ListMongoCollections",
                description="Use this tool to list all MongoDB collection names for investigation."
            )
        
        mongo_vector_search_tool = Tool.from_function(
                func=vector_search_across_collections,
                name="VectorSearchIncidents",
                description="""Use this tool to semantically search across incident summaries and recommendations in MongoDB.
Input format:
{
  "collection": "Incident Report INCXXXXXX",
  "query": "privilege escalation attempt"
}
It returns the most semantically relevant incident entries from that collection.
"""
            )

        # tools_box = toolkit.get_tools()
        # print(f"tools_box: {tools_box}")
        # tools_box.append(mongo_fulltext_tool)

        tools_box = [mongo_collection_list_tool, mongo_vector_search_tool]

        # Pull prompt (or define your own)
        system_message = MONGODB_AGENT_SYSTEM_PROMPT.format(top_k=5)


        # Custom prompt for your own use-case
        chatbot_agent = create_react_agent(
            model=OPENAI_LLM,
            # tools=tools_box,
            # tools=tools,
            # state_modifier=system_message,
            prompt = """
You are a SOC (Security Operations Center) Analyst AI assistant. Your role is to help users investigate cybersecurity threats and incidents using logs stored in a MongoDB database. Follow these instructions carefully.

You have access to the MongoDB database. These are details about the MongoDB environment: {mongodb}  
Use this `{id}` as the identifier to locate and analyze relevant security data. Your job is to answer any query related to this incident or context to the best of your ability.

When handling user queries, adhere to the following guidelines:
   a. Always base your responses strictly on the information retrieved from the MongoDB database.
   b. Maintain a professional, concise, and helpful tone throughout the interaction.

**IMPORTANT**: If you're asked to generate a Security Incident Report, construct it using the relevant fields (such as `summary`, `impact`, `threat_type`, `detected_at`, etc.) from the available logs in the database.

Format your responses as follows:
   a. Clearly reference the relevant parts of the incident data in your answer.
   b. If helpful, provide a structured summary including threat type, impact, and any notable behaviors or indicators.
   c. Offer additional context only if it is supported by the data.

To address a user query, follow this procedure:
   a. Carefully read and understand the user's question.
   b. Use your tools to inspect the schema and structure of the collection if necessary.
   c. Identify and extract the most relevant information from the logs.
   d. Formulate a factual and concise response.
   e. Confirm that your answer is strictly grounded in the provided data.
   f. Present your findings clearly to the user.

These are additional MongoDB environment details to help you operate accurately: {mongodb}
""".format(id=id, mongodb=system_message),
            tools=toolkit.get_tools(),
        )

        # Invoke the chatbot logic
        result = await chatbot_agent.ainvoke(state)
        # LOGGER.debug(result)

        return Command(
            update={"messages": [AIMessage(content=result["messages"][-1].content, name=ChatbotAgent.agent_name)]},
            goto=END,
        )
