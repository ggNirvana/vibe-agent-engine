from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes.planner import brand_planner
from .nodes.coder import code_architect
from .nodes.inspector import inspector

# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("planner", brand_planner)
workflow.add_node("coder", code_architect)
workflow.add_node("auditor", inspector)

# Add edges
workflow.set_entry_point("planner")
workflow.add_edge("planner", "coder")
workflow.add_edge("coder", "auditor")
workflow.add_edge("auditor", END)

# Compile
agent_workflow = workflow.compile()
