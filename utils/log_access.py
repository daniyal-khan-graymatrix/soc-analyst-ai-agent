import json
from datetime import datetime
import os

AUDIT_LOG_PATH = "audit_logs/log.jsonl"
os.makedirs("audit_logs", exist_ok=True)

def log_access(report_name: str, user: str = "frontend_user"):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "report_name": report_name,
        "accessed_by": user,
        "action": "viewed"
    }
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
