import hashlib
import json

def hash_log_entry(entry: dict) -> str:
    """
    Returns SHA-256 hash of a JSON-safe dictionary (sorted for consistency).
    """
    entry_str = json.dumps(entry, sort_keys=True)
    return hashlib.sha256(entry_str.encode("utf-8")).hexdigest()
