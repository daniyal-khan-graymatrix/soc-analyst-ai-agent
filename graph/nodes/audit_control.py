import uuid
from datetime import datetime
from utils.hashing import hash_log_entry
from utils.logger import append_audit_log
from utils.rbac import is_authorized


def audit_control_agent(state):
    """
    AuditControlAgent:
    - Enforces RBAC before allowing access to incident report export
    - Generates a single immutable audit log entry (if RBAC passes)

    Expected in state:
    - state['accessed_by']: str (analyst email)
    - state['user_role']: str

    Output:
    - state['audit_log']: dict of audit entry (or None if RBAC fails)
    - state['rbac_passed']: True/False
    - state['report_filename']: the generated filename to use for report export
    """
    analyst_email = state.get("accessed_by")
    role = state.get("user_role")

    if not is_authorized(role):
        print("RBAC failed: Response access denied.")
        state["rbac_passed"] = False
        state["audit_log"] = None
        return state

    incident_id = f"INC{str(uuid.uuid4())[:8].upper()}"
    report_filename = f"Incident Report {incident_id}.json"

    log_entry = {
        "event": f"Exported Incident Report {incident_id}",
        "accessed_by": analyst_email,
        "timestamp": datetime.now().isoformat(),
        "access_type": "export",
        "report_classification": "High Risk",
        "justification_required": True,
        "compliance_flag": "RBI-CSF/ISO27001"
    }

    hash_value = hash_log_entry(log_entry)
    append_audit_log(log_entry, hash_value)

    state["report_filename"] = report_filename
    state["rbac_passed"] = True
    return state
