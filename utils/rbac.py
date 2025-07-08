def is_authorized(role: str, classification: str = None) -> bool:
    """
    Enforces RBAC: Only L3 or Admin can access sensitive reports.

    If classification is provided and is sensitive, only L3/ADMIN can access.
    If not provided, defaults to general role check (used during export).
    """
    if classification:
        sensitive = classification.lower() in ["plp access", "privilege escalation"]
        return role.upper() in ["L3", "ADMIN"] if sensitive else True
    return role.upper() in ["L3", "ADMIN"]
