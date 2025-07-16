from typing import List, Optional, Dict
import numpy as np
from pymongo import MongoClient
from langchain.tools import Tool
from langchain_mongodb.retrievers.full_text_search import MongoDBAtlasFullTextSearchRetriever
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Connect to MongoDB Atlas
client = MongoClient(os.getenv("MongoUrl"))
db = client["soc_incidents"]

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
embedding_model = "text-embedding-3-small"

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
        response = openai_client.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return []

def vector_search_across_collections(input: dict) -> Dict[str, List[Dict]]:
    """
    This function receives a dictionary with:
    - 'collection': List[str] – collection names to search
    - 'query': str – the search query

    It returns a dictionary of collection names and top matching documents
    with cosine similarity >= SIMILARITY_THRESHOLD.
    """
    SIMILARITY_THRESHOLD = 0.1  # minimum similarity required to include a result

    try:
        search_collections = input.get("collection")
        query = input.get("query")

        if not search_collections or not isinstance(search_collections, list):
            raise ValueError("You must pass a list of collection names in the 'collection' field.")

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
                    continue

                try:
                    score = np.dot(doc_emb, query_embedding) / (
                        np.linalg.norm(doc_emb) * np.linalg.norm(query_embedding)
                    )
                    if score >= SIMILARITY_THRESHOLD:
                        doc.pop("embedding", None)  # Remove embedding before return
                        scored_docs.append((score, doc))
                except Exception as e:
                    print(f"Skipping doc due to scoring error: {e}")

            top_matches = sorted(scored_docs, key=lambda x: x[0], reverse=True)
            if top_matches:
                results[col_name] = [doc for _, doc in top_matches]

        return results

    except Exception as e:
        return {"error": f"Vector search failed: {str(e)}"}
