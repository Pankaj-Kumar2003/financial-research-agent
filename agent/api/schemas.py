from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ResearchRequest(BaseModel):
    ticker: str = Field(..., example="AAPL", description="Stock ticker symbol")
    user_feedback: Optional[str] = Field(None, example="Focus heavily on AI competition", description="Optional steering instructions for the Coordinator agent")
    use_cache: bool = Field(True, description="Whether to check Redis cache before running agent pipeline")

class ResearchResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    summary: Optional[str] = None
    final_report: str
    telemetry: Dict[str, Any] = Field(default_factory=dict)
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AskRequest(BaseModel):
    ticker: str = Field(..., example="AAPL")
    question: str = Field(..., example="What are the main risks with Taiwan manufacturing?")
    chat_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class AskResponse(BaseModel):
    ticker: str
    question: str
    answer: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    cache: str
    version: str = "1.0.0"

