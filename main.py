# main.py
import json
from graph.flow import build_graph
from state_schema import State

# Load sample data
def load_logs():
    with open("data/mobile_app_logs_2025-06-30.json") as f1, open("data/internal_plp_logs_2025-06-30.json") as f2:
        mobile_logs = json.load(f1)
        plp_logs = json.load(f2)
    return mobile_logs + plp_logs

# Simulate a run context
def get_initial_state():
    logs = load_logs()
    state = State(logs=logs, accessed_by="l3_analyst@bank.co.in", user_role="L3")
    return state

def main():
    flow = build_graph()
    initial_state = get_initial_state()
    flow.invoke(initial_state)


if __name__ == "__main__":
    main()
