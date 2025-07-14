import json
import os
from pathlib import Path
from graph.flow import build_graph
from state_schema import State
from csvtojson import csv_to_json  # This function should return a list of dicts

DATA_DIR = Path("data")

def load_logs():
    all_logs = []

    for file_path in DATA_DIR.rglob("*"):  # includes subfolders
        if file_path.is_file():
            try:
                if file_path.suffix == ".json":
                    with open(file_path, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                        if isinstance(logs, dict):
                            logs = [logs]
                        all_logs.extend(logs)
                elif file_path.suffix == ".csv":
                    logs = csv_to_json(str(file_path))
                    all_logs.extend(logs)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

    return all_logs

def get_initial_state():
    logs = load_logs()
    return State(logs=logs, accessed_by="l3_analyst@bank.co.in", user_role="L3")

def main():
    flow = build_graph()
    initial_state = get_initial_state()
    flow.invoke(initial_state)

if __name__ == "__main__":
    main()
