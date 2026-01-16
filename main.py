from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uuid
import os
import asyncio

try:
    from .workflow import agent_workflow
    from .state import AgentState
except ImportError:
    # Fallback for direct execution
    from workflow import agent_workflow
    from state import AgentState

app = FastAPI(title="VibeInvite Agent Engine")

class PhotoMetadata(BaseModel):
    description: Optional[str] = None
    # No URL included to protect privacy

# Minimal Request Structure - Style Preferences Only + Photo Metadata
class GenerateRequest(BaseModel):
    request_id: str
    theme: str
    color: str
    layout: str
    photos: List[PhotoMetadata] = []

class GenerateResponse(BaseModel):
    status: str
    message: str
    request_id: str

SHARED_STORAGE_PATH = "../vibe-artifacts-h5/outputs"

async def run_workflow_task(request_data: GenerateRequest):
    """
    Background task to run the LangGraph workflow.
    """
    request_id = request_data.request_id
    print(f"[{request_id}] Starting workflow...")
    
    # Reconstruct preferences
    preferences = {
        "style": request_data.theme,
        "primary_color": request_data.color,
        "page_format": request_data.layout
    }
    
    # Pass photo metadata (descriptions only) to assets
    assets = {
        "photos": [p.dict() for p in request_data.photos]
    }
    
    # Map request data to AgentState
    # No user data passed to Agent
    initial_state: AgentState = {
        "request_id": request_id,
        "user_story": "", # Empty
        "preferences": preferences,
        "assets": assets, 
        "brand_plan": None,
        "html_content": None,
        "audit_report": None,
        "current_step": "START"
    }
    
    try:
        final_state = await agent_workflow.ainvoke(initial_state)
        
        # Save output
        html_content = final_state.get("html_content")
        if html_content:
            output_file = os.path.join(SHARED_STORAGE_PATH, f"{request_id}.html")
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"[{request_id}] Saved to {output_file}")
            
        print(f"[{request_id}] Workflow completed.")
        
    except Exception as e:
        print(f"[{request_id}] Workflow failed: {e}")

@app.post("/generate", response_model=GenerateResponse)
async def generate_invite(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Endpoint called by Java Server to trigger agent generation.
    """
    # Trigger background task
    background_tasks.add_task(run_workflow_task, request)
    
    return {
        "status": "accepted",
        "message": "Agent workflow started",
        "request_id": request.request_id
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
