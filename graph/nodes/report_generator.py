import json
import os

def report_generator(state):
    """
    ReportGenerator: Aggregates all detected incidents into a final incident summary report,
    and writes the incident summary to a uniquely named JSON file based on report_filename.

    Expected Inputs (in `state`):
    - 'logs': List of full structured incidents
    - 'report_filename': name of the file to export (e.g., "Incident Report INCxxxx.json")

    Output:
    - state['logs']: List[Dict] containing formatted incidents and recommendations
    """
    incidents = state.get("logs", [])
    filename = state.get("report_filename", "Incident Report UNKNOWN.json")

    # Format flat incident summary list
    summary_report = []
    for incident in incidents:
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
        summary_report.append(summary)

    # Save to file
    os.makedirs("reports", exist_ok=True)
    with open(f"reports/{filename}", "w") as f:
        json.dump(summary_report, f, indent=2)

    return state
