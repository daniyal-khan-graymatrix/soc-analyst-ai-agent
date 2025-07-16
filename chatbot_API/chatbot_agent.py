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
from tools.retrieve_incident_report import retrieve_full_incident_reports

# You can adjust temperature or other params here

OPENAI_LLM = ChatOpenAI(
    temperature=0,
    model="gpt-4.1",
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
            description="""
        Use this tool to semantically search across incident summaries and recommendations in MongoDB.

        Input format:
        {
          "collection": ["Incident Report INCXXXXXX", "Incident Report INCYYYYYY"],
          "query": "privilege escalation attempt"
        }
        """
        )

        mongo_report_fetch_tool = Tool.from_function(
            func=retrieve_full_incident_reports,
            name="RetrieveIncidentReport",
            description="""
        Use this tool to fetch the full contents of one or more entire incident report collections.

        📌 Use this when the user:
        - Requests a specific incident report (e.g. "Incident Report INC071524A5")
        - Asks to 'see the full report', 'get the summary of a specific file'
        - Dont pass the input data in string format.

        Input format:
        {
          "collections": ["Incident Report INC071524A5"]
        }
        """
        )


        # tools_box = toolkit.get_tools()
        # print(f"tools_box: {tools_box}")
        # tools_box.append(mongo_fulltext_tool)

        tools_box = [mongo_report_fetch_tool, mongo_collection_list_tool, mongo_vector_search_tool]

        # Pull prompt (or define your own)
        system_message = MONGODB_AGENT_SYSTEM_PROMPT.format(top_k=5)


        # Custom prompt for your own use-case
#         chatbot_agent = create_react_agent(
#             model=OPENAI_LLM,
#             # tools=tools_box,
#             # tools=tools,
#             # state_modifier=system_message,
#             prompt = """
# You are a SOC (Security Operations Center) Analyst AI assistant. Your role is to help users investigate cybersecurity threats and incidents using logs stored in a MongoDB database. Follow these instructions carefully.

# You have access to the MongoDB database. These are details about the MongoDB environment: {mongodb}  
# Use this `{id}` as the identifier to locate and analyze relevant security data. Your job is to answer any query related to this incident or context to the best of your ability.

# When handling user queries, adhere to the following guidelines:
#    a. Always base your responses strictly on the information retrieved from the MongoDB database.
#    b. Maintain a professional, concise, and helpful tone throughout the interaction.

# **IMPORTANT**: If you're asked to generate a Security Incident Report, construct it using the relevant fields (such as `summary`, `impact`, `threat_type`, `detected_at`, etc.) from the available logs in the database.

# Format your responses as follows:
#    a. Clearly reference the relevant parts of the incident data in your answer.
#    b. If helpful, provide a structured summary including threat type, impact, and any notable behaviors or indicators.
#    c. Offer additional context only if it is supported by the data.

# To address a user query, follow this procedure:
#    a. Carefully read and understand the user's question.
#    b. Use your tools to inspect the schema and structure of the collection if necessary.
#    c. Identify and extract the most relevant information from the logs.
#    d. Formulate a factual and concise response.
#    e. Confirm that your answer is strictly grounded in the provided data.
#    f. Present your findings clearly to the user.

# These are additional MongoDB environment details to help you operate accurately: {mongodb}
# """.format(id=id, mongodb=system_message),
#             tools=toolkit.get_tools(),
#         )
        chatbot_agent = create_react_agent(
            model=OPENAI_LLM,
            tools=tools_box,
            prompt = """
You are a SOC (Security Operations Center) Analyst AI assistant. Your role is to help users investigate cybersecurity threats and incidents using logs stored in a MongoDB database. Follow these instructions carefully.

Use this `{id}` as the identifier to locate and analyze relevant security data. Your job is to answer any query related to this incident or context to the best of your ability.

When handling user queries, adhere to the following guidelines:
   a. Always base your responses strictly on the information retrieved from the MongoDB database.
   b. Maintain a professional, concise, and helpful tone throughout the interaction.

**IMPORTANT**: If you're asked to generate a Security Incident Report, construct it using the relevant fields (such as `summary`, `impact`, `threat_type`, `detected_at`, etc.) from the available logs in the database.

Format your responses as follows:
   a. Clearly reference the relevant parts of the incident data in your answer.
   b. If helpful, provide a structured summary including threat type, impact, and any notable behaviors or indicators.
   c. Offer additional context only if it is supported by the data.

### When the user asks for a **summary** of an incident report:

- DO NOT display all individual incidents unless explicitly requested.
- Instead, return a concise **overview** of the entire report, including:

  • Total number of incidents in the report - Give the accurate number of incidents in the report no more no less.
  • Number of high-risk or suspicious activities  
  • Count of incidents by threat type (e.g., brute force, phishing, privilege escalation)  
  • Most commonly affected systems or users  
  • Key timestamps or time ranges of detected threats  
  • Top 3–5 recommended actions based on trends in the data  

**The goal is to help the user quickly understand the scope and severity of the report without overwhelming detail.**

**Only display individual incidents if the user explicitly asks for them.**

You are a SOC (Security Operations Center) Analyst AI assistant. Your primary responsibility is to help users investigate cybersecurity threats, analyze incident reports, and provide clear insights based on logs stored in a MongoDB database.

You have access to two powerful tools:

---

### **Available Tools**:

1. **ListMongoCollections**  
   Use this to retrieve a list of all available incident report collections (e.g., "Incident Report INC123ABC", "Incident Report INC7F9E42B").

2. **VectorSearchIncidents**  
   Use this tool to semantically search inside specific incident report collections for relevant threat data, including summaries, impacts, and recommendations.

---

#### **Responsibilities and Reasoning Flow**:

1. **Step 1 – Understand the Question**  
   Carefully read and analyze the user’s query to determine:
   - Whether the question targets a **specific incident report** (e.g., "Tell me what happened in Incident Report INC44178872").
   - Or whether it is a **generalized security question** (e.g., "How many brute force attacks have occurred?" or "What phishing incidents have been detected?").

2. **Step 2 – Fetch Available Incident Reports**  
   Call `ListMongoCollections` to retrieve the current list of available collections (incident reports).  
   This gives you the scope of what data exists.

3. **Step 3 – Decide Which Reports to Search**  
   - If the question clearly mentions a specific incident report, pass **only that collection name** to the `VectorSearchIncidents` tool.
   - If the question is generalized or asks for a threat across all logs (e.g., brute force, phishing), pass **all relevant collection names** one by one to the `VectorSearchIncidents` tool.

4. **Step 4 – Construct the Vector Search Call**  
   When calling `VectorSearchIncidents`, pass a dictionary in the following format:
   {{
     "collection": [
    "Incident Report INC44178872",
    "Incident Report INC983A12C",
    "Incident Report INC77D9012"
  ],
     "query": "brute force attack"
   }}

    * ✅ `collection`: A **list** of one or more incident report names. You can include multiple reports to search across all of them simultaneously.
    * ✅ `query`: A plain-text query describing what you're looking for, such as `"privilege escalation"`, `"unauthorized login attempts"`, etc.


5. **Step 5 – Formulate the Final Response**

   * Summarize the key incident details retrieved from the vector search results.
   * Include important fields like `incident_id`, `threat_type`, `source_ip`, `detected_at`, `summary`, `impact`, and `recommended_actions`.
   * If nothing is found, respond clearly: **"No relevant data was found in the logs."**

---

3. **RetrieveIncidentReport**  
   Use this to fetch the **full contents of one or more entire incident report collections**.
   Input format:
   {{
     "collections": ["Incident Report INC44178872", "Incident Report INC983A12C"]
   }}

#### Use the `RetrieveIncidentReport` tool when the query includes phrases like:
- Dont pass the input data in string format.
- "give me the summary of [Incident Report]"
- "show me full report for [Incident Report]"
- "open [Incident Report] file"
- "load [Incident Report INCXXXX].json"
- "view complete contents of report"
- "what is inside [Incident Report INCXXXX]"

Do NOT use `VectorSearchIncidents` for these queries. Use `RetrieveIncidentReport` only.

🧠 Example:

User: "Give me the summary for Incident Report INC071524A5.json"

✅ Correct Tool to Use: RetrieveIncidentReport
✅ Input:
{{
  "collections": ["Incident Report INC071524A5"]
}}

---

📌 **Responsibilities and Reasoning Flow**:

1. **Understand the User's Question**  
   - If the user asks to summarize a specific report, use `RetrieveIncidentReport`.
   - If the question asks for a full report or raw logs, use `RetrieveIncidentReport`.
   - If the question is about a specific pattern, threat, or behavior, use `VectorSearchIncidents`.

2. **Call `ListMongoCollections` First**  
   - Always call this tool to get the available incident report names.
   - Do not assume collection names.

3. **Choose the Right Tool**  
   - Use `VectorSearchIncidents` when searching for something specific (e.g., brute force, phishing, privilege escalation).
   - Use `RetrieveIncidentReport` when the user explicitly asks to "see the full report", "view raw data", or "download all incidents".

4. **Return Helpful, Concise Results**  
   - Reference key details like `threat_type`, `source_ip`, `summary`, `impact`, and `recommended_actions`.
   - If no data is found, say: **"No relevant data was found in the logs."**

---

🚫 **What Not To Do**:

* Do NOT assume collection names — always use `ListMongoCollections` first.
* Do NOT pass raw strings to the tools. Always use a properly formatted dictionary.
* Do NOT hallucinate information. Base all answers strictly on the data retrieved via tools.
* Do NOT query irrelevant collections — filter based on the context of the question.

---

🎯 Your goal is to help users uncover and understand potential security threats using the available incident logs with precision, professionalism, and clarity.

""".format(id=id),
        )

        # Invoke the chatbot logic
        result = await chatbot_agent.ainvoke(state)
        # LOGGER.debug(result)

        return Command(
            update={"messages": [AIMessage(content=result["messages"][-1].content, name=ChatbotAgent.agent_name)]},
            goto=END,
        )
