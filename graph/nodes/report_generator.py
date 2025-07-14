import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

load_dotenv()

# Setup MongoDB
client = MongoClient(os.getenv("MongoUrl"))
db = client["soc_incidents"]

# Setup OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
embedding_model = "text-embedding-3-small"
# collection_name = "Incidents"

def generate_embedding(text):
    try:
        response = openai_client.embeddings.create(
            model=embedding_model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return []

def report_generator(state):
    print("Report Generation: generating report .......")

    incidents = state.get("logs", [])
    filename = state.get("report_filename", "Incident Report UNKNOWN.json")
    report_name = filename.replace(".json", "")
    collection_name = filename.replace(".json", "")

    summary_report = []

    for incident in tqdm(incidents, desc="Generating embeddings"):
        summary = {
            "incident_id": incident.get("incident_id"),
            "threat_type": incident.get("threat_type"),
            "affected_user": incident.get("affected_user"),
            "source_ip": incident.get("source_ip"),
            "system": incident.get("system"),
            "endpoint": incident.get("endpoint"),
            "detected_at": incident.get("detected_at"),
            "summary": incident.get("summary"),
            "impact": incident.get("impact"),
            "event_type": incident.get("event_type"),
            "recommended_actions": incident.get("recommended_actions", []),
            "why_these_recommendations": incident.get("why_these_recommendations", "")
        }

        # Create the embedding input
        embed_input = " ".join(
            str(v) for k, v in summary.items()
            if k not in {"incident_id", "detected_at"} and v
        )

        # summary["embedding"] = generate_embedding(embed_input)
        summary["report_name"] = report_name
        summary_report.append(summary)

    # Save JSON file (without embedding or report_name)
    clean_report = [
        {k: v for k, v in incident.items() if k not in {"embedding", "report_name"}}
        for incident in summary_report
    ]
    os.makedirs("reports", exist_ok=True)
    with open(f"reports/{filename}", "w") as f:
        json.dump(clean_report, f, indent=2)
    print(f"Incident report is stored as: reports/{filename}")

    # Insert to MongoDB
    if summary_report:
        db[collection_name].insert_many(summary_report)
        print(f"Inserted {len(summary_report)} incidents into MongoDB collection: {collection_name}")

    return state
