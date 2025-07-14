from typing import List, Optional, Dict
import numpy as np
from pymongo import MongoClient
from langchain.tools import Tool
from langchain_mongodb.retrievers.full_text_search import MongoDBAtlasFullTextSearchRetriever
import os, openai
from dotenv import load_dotenv
load_dotenv()

# Connect to MongoDB Atlas
client = MongoClient(os.getenv("MongoUrl"))
db = client["soc_incidents"]

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list:
    """
    Generate an embedding vector for the given text using OpenAI Embedding API.

    Args:
        text (str): The text to embed.
        model (str): The embedding model name.

    Returns:
        list: Embedding vector.
    """
    try:
        text = text.replace("\n", " ")
        response = openai.Embedding.create(input=[text], model=model)
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return []



def vector_search_across_collections(
    query: str,
    top_k: int = 3,
    search_collections: Optional[List[str]] = None
) -> Dict[str, List[Dict]]:
    query_embedding = np.array(get_embedding(query))
    results = {}

    for col_name in search_collections:
        collection = db[col_name]
        docs = list(collection.find())
        if not docs:
            continue

        scored_docs = []
        for doc in docs:
            doc_emb = np.array(doc.get("embedding", []))
            if doc_emb.size != query_embedding.size:
                continue  # skip mismatched or invalid embeddings

            try:
                score = np.dot(doc_emb, query_embedding) / (
                    np.linalg.norm(doc_emb) * np.linalg.norm(query_embedding)
                )
                scored_docs.append((score, doc))
            except Exception as e:
                print(f"Skipping doc due to scoring error: {e}")

        top_matches = sorted(scored_docs, key=lambda x: x[0], reverse=True)[:top_k]
        if top_matches:
            results[col_name] = [doc for _, doc in top_matches]

    return results