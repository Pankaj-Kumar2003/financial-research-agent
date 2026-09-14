from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ResearchState(BaseModel):
    """
    Shared Blackboard State for the Multi-Agent Pipeline.
    Passes contextual data and intermediary results between agents.
    """
    ticker: str
    
    # Raw data gathered by the DataGatheringAgent
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Individual reports/thoughts from specialized analyst agents
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # The final synthesized report
    final_report: Optional[str] = None
    
    # Conversational memory for interactive Q&A
    chat_history: List[Dict[str, str]] = Field(default_factory=list)
    
    # Custom instructions provided by the user mid-pipeline
    user_feedback: Optional[str] = None
    
    # Non-fatal errors or warnings encountered during execution
    errors: List[str] = Field(default_factory=list)

