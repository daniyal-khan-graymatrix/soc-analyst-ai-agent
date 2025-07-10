from pymongo import MongoClient
from langchain.tools import Tool
from langchain_mongodb.retrievers.full_text_search import MongoDBAtlasFullTextSearchRetriever
import os, json
from dotenv import load_dotenv
load_dotenv()

# Connect to MongoDB Atlas
client = MongoClient(os.getenv("MongoUrl"))
db = client["soc_incidents"]


def fulltext_query_tool(input):
    """
    Handles full-text search queries from LangChain agent.
    Accepts either a dict or a stringified dict.

    Expected format:
    {
        "collection": "Incident Report INCxxxxx",
        "query": "unauthorized access to user accounts",
        "search_field":  "thread_type" or "summary"
        "search_index_name": "default"
    }
    """
    try:
        # Parse string input if needed
        if isinstance(input, str):
            input = json.loads(input)

        collection = db[input["collection"]]
        retriever = MongoDBAtlasFullTextSearchRetriever(
            collection=collection,
            search_field=input.get("search_field", "summary"),
            search_index_name=input.get("search_index_name", "default")
        )
        results = retriever.invoke(input["query"])
        return [doc for doc in results] if results else "No matches found."

    except Exception as e:
        return f"Full-text search failed: {str(e)}"
