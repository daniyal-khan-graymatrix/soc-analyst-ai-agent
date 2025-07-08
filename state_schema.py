from typing import TypedDict, List, Dict

class State(TypedDict):
    # Input (loaded at start)
    logs: List[Dict]                # Raw logs from mobile/PLP systems
    accessed_by: str                # Analyst email or ID (e.g. "l3_analyst@bank.co.in")
    user_role: str                  # Analyst's role (e.g. "L1", "L3", "Admin")

    # audit_control
    audit_log: Dict                # Contains audit entry + SHA-256 hash
    rbac_passed: bool              # Whether response agent is allowed to proceed

    # File name
    report_filename: str