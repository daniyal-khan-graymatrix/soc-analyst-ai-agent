from typing import List
from pymongo import MongoClient
from langchain.tools import Tool
from langchain_mongodb.retrievers.full_text_search import MongoDBAtlasFullTextSearchRetriever
import os, json
from dotenv import load_dotenv
load_dotenv()

# Connect to MongoDB Atlas
client = MongoClient(os.getenv("MongoUrl"))
db = client["soc_incidents"]


def get_collection_names(_: dict = None) -> list:
    """Retrieve list of MongoDB collections in the `soc_incidents` database."""
    return db.list_collection_names()
