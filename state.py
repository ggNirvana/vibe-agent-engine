from typing import TypedDict, Dict, Any, Optional

# Define the state
class AgentState(TypedDict):
    request_id: str
    user_story: str
    preferences: Dict[str, Any]
    assets: Dict[str, Any]
    
    # Outputs from agents
    brand_plan: Optional[Dict[str, Any]]
    html_content: Optional[str]
    audit_report: Optional[Dict[str, Any]]
    
    current_step: str
