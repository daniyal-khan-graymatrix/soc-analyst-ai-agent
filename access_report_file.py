from utils.rbac import is_authorized
from utils.hashing import hash_log_entry
from utils.logger import append_audit_log
from datetime import datetime
import json
import os

def access_report_file(filename: str, user_email: str, user_role: str) -> dict:
    """
    Secure accessor for incident report JSON files.
    - Logs access attempt
    - Enforces RBAC (L3/ADMIN only)
    - Returns file content if allowed
    """

    if not is_authorized(user_role):
        print(f"[ACCESS DENIED] {user_email} tried to access {filename}")
        return {"error": "Access denied. Insufficient role."}

    filepath = os.path.join("reports", filename)
    if not os.path.exists(filepath):
        return {"error": "Report not found."}

    with open(filepath, "r") as f:
        data = json.load(f)

    # Record immutable audit log
    audit_entry = {
        "event": f"Accessed {filename}",
        "accessed_by": user_email,
        "timestamp": datetime.now().isoformat(),
        "access_type": "read",
        "report_classification": "High Risk",
        "justification_required": True,
        "compliance_flag": "RBI-CSF/ISO27001"
    }
    hash_value = hash_log_entry(audit_entry)
    append_audit_log(audit_entry, hash_value)

    return {"data": data}

result = access_report_file("Incident Report INC62A6084C.json", "analyst@bank.co.in", "L3")
print(result)