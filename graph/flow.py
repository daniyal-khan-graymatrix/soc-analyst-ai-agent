from langgraph.graph import StateGraph, END
from state_schema import State
from graph.nodes.threat_detector import threat_detector_agent
from graph.nodes.incident_manager import incident_manager_agent
from graph.nodes.audit_control import audit_control_agent
from graph.nodes.response_recommender import response_recommender_agent
from graph.nodes.report_generator import report_generator


def build_graph():
    graph = StateGraph(State)

    # Register nodes
    graph.add_node("detect", threat_detector_agent)
    graph.add_node("context", incident_manager_agent)
    graph.add_node("audit", audit_control_agent)
    graph.add_node("response", response_recommender_agent)
    graph.add_node("report", report_generator)

    # Define entry point
    graph.set_entry_point("detect")

    # Static edges
    graph.add_edge("detect", "context")
    graph.add_edge("context", "audit")
    graph.add_conditional_edges("audit", lambda state: "response" if state.get("rbac_passed", False) else "end", {
        "response": "response",
        "end": END
    })
    graph.add_edge("response", "report")
    graph.add_edge("report", END)

    return graph.compile()
