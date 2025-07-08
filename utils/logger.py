import json
import os
from datetime import datetime

LOG_FILE = "audit_logs/log.jsonl"

os.makedirs("audit_logs", exist_ok=True)

def append_audit_log(entry: dict, hash_value: str):
    """
    Appends an immutable audit entry with its SHA-256 hash to a local JSONL file.
    In production, this should be stored in append-only storage.
    """
    log_record = {
        "timestamp": datetime.now().isoformat(),
        "entry": entry,
        "sha256_hash": hash_value
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_record) + "\n")
