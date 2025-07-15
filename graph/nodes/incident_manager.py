import uuid
import os
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()

# Setup LangChain LLM instance
llm = ChatOpenAI(model="gpt-4o", temperature=0.2, api_key=os.getenv("OPENAI_API_KEY"))

# LangChain Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a security incident triage assistant. Analyze logs to identify threats, correlate similar events, assess risk, and return incident records."),
    ("user", """
You are given a list of suspicious logs. For each log, return a JSON object with:
- threat_type 
- affected_user
- source_ip
- affected_system 
- endpoint 
- timestamp
- summary (1–2 sentence explanation)
- impact (business impact)
- risk_score (1–10)
- event_type

Output a list of such JSON objects (one per log).

Logs:
{logs}
    """)
])


def classify_logs_with_llm(logs):
    try:
        chain = prompt | llm
        response = chain.invoke({"logs": json.dumps(logs)})
        content = response.content.strip()

        # Strip code block if present
        if content.startswith("```json"):
            content = content[7:].strip()  # remove ```json
        if content.endswith("```"):
            content = content[:-3].strip()  # remove ```

        return json.loads(content)
    except Exception as e:
        print(f"[LLM Incident Manager] Error: {e}")


# # LangChain Prompt Template (per log)
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are a SOC analyst assistant. Your job is to classify a suspicious log entry and assess its risk."),
#     ("user", """
# Given the following suspicious log, return a JSON object with:
# - threat_type (e.g., brute_force, plp_access, unknown_activity, malicious_transfer)
# - affected_system (e.g., internal_plp, mobile_app)
# - summary (1–2 sentence explanation)
# - impact (business impact)
# - risk_score (1–10)

# Log:
# {logs}
#     """)
# ])

# def classify_logs_with_llm(logs):
#     chain = prompt | llm
#     results = []

#     for log in logs:
#         try:
#             response = chain.invoke({"logs": json.dumps([log])})
#             content = response.content.strip()

#             # Clean LLM markdown formatting if present
#             if content.startswith("```json"):
#                 content = content[7:].strip()
#             if content.endswith("```"):
#                 content = content[:-3].strip()

#             parsed = json.loads(content)

#             # LLM may return a list of one item
#             if isinstance(parsed, list) and len(parsed) == 1:
#                 parsed = parsed[0]
#             results.append(parsed)

#         except Exception as e:
#             # print(f"[LLM Fallback] Log failed: {log.get('user')} → {e}")
#             # endpoint = log.get("endpoint", "")
#             # threat_type = "brute_force" if log.get("reason") == "Brute force suspected" else "plp_access" if "/plp" in endpoint else "generic_suspicious_activity"
#             # results.append({
#             #     "threat_type": threat_type,
#             #     "affected_system": "internal_plp" if "/plp" in endpoint else "mobile_app",
#             #     "summary": f"{threat_type.replace('_', ' ').title()} detected via fallback rules.",
#             #     "impact": "Potential unauthorized access or misuse.",
#             #     "risk_score": 5
#             # })
#             pass

#     return results


def incident_manager_agent(state):
    """
    IncidentManagerAgent: Batches suspicious logs (10 at a time), analyzes them using GPT-4o,
    and returns structured incident reports.

    Input:
    - state['logs']: List of suspicious logs

    Output:
    - state['logs']: List of structured incident dicts
    """
    suspicious_logs = state.get("logs", [])
    print(f"Length of suspicious log: {len(suspicious_logs)}")
    if not suspicious_logs:
        state["logs"] = []
        return state

    incidents = []

    # Process logs in batches of 10
    batch_size = 10
    for i in range(0, len(suspicious_logs), batch_size):
        batch = suspicious_logs[i:i + batch_size]
        try:
            enriched_batch = classify_logs_with_llm(batch)
        except Exception as e:
            print(f"Batch {i//batch_size + 1} failed: {e}")
            continue

        for log, analysis in zip(batch, enriched_batch):
            incident_id = f"INC{str(uuid.uuid4())[:8].upper()}"
            report = {
                "incident_id": incident_id,
                "threat_type": analysis.get("threat_type", "Unknown").replace("_", " ").title(),
                "affected_user": analysis.get("affected_user", "Unknown"),
                "source_ip": analysis.get("source_ip", "Unknown"),
                "system": analysis.get("affected_system", log.get("HOSTNAME", "Unknown")),
                "endpoint": analysis.get("endpoint", "Unknown"),
                "detected_at": analysis.get("timestamp", log.get("TIMESTAMP", "Unknown")),
                "summary": analysis.get("summary", log.get("MESSAGE", "No message")),
                "impact": analysis.get("impact", "Unknown"),
                "risk_score": analysis.get("risk_score", "Medium"),
                "event_type": log.get("event") or log.get("LEVEL", "Info")
            }
            incidents.append(report)

    # Save the incidents and enrich the data
    state["logs"] = incidents
    return state
