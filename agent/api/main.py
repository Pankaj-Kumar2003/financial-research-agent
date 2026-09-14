from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict, Any

from agent.api.schemas import (
    ResearchRequest, ResearchResponse,
    AskRequest, AskResponse,
    HealthResponse
)
from agent.pipeline import run_multi_agent_pipeline
from agent.db.cache import cache_manager
from agent.db.database import get_db, SessionLocal
from agent.db.models import ResearchBrief, Query
from agent.llm import call_llm_chat

app = FastAPI(
    title="Financial Research Agent API",
    description="Institutional-grade autonomous multi-agent equity research and financial analytics REST service.",
    version="1.0.0"
)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
def health_check():
    """Health check endpoint monitoring database and cache connectivity."""
    db_status = "connected"
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception:
        db_status = "sqlite/active"
        
    cache_status = "redis_connected" if cache_manager.redis_client else "in_memory_active"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        database=db_status,
        cache=cache_status,
        version="1.0.0"
    )

@app.post("/research", response_model=ResearchResponse, tags=["Research"])
def generate_research(request: ResearchRequest):
    """
    Executes the autonomous multi-agent pipeline for a stock ticker.
    Checks Redis cache first if use_cache is True.
    """
    ticker = request.ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty.")
        
    try:
        # Run the multi-agent pipeline with optional steering feedback
        state = run_multi_agent_pipeline(
            ticker=ticker,
            interactive_feedback=False,
            use_cache=request.use_cache
        )
        
        # Apply user steering if provided and cached was bypassed
        if request.user_feedback and not request.use_cache:
            state.user_feedback = request.user_feedback
            from agent.agents.coordinator_agent import SynthesisCoordinatorAgent
            state = SynthesisCoordinatorAgent().run(state)
            
        return ResearchResponse(
            ticker=ticker,
            company_name=state.raw_data.get("stock_data", {}).get("short_name", ticker),
            summary=state.final_report[:300] + "..." if state.final_report else "No summary available.",
            final_report=state.final_report,
            telemetry=state.raw_data.get("telemetry", {}),
            raw_data=state.raw_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research generation failed: {str(e)}")

@app.get("/research/{ticker}", response_model=ResearchResponse, tags=["Research"])
def get_existing_research(ticker: str):
    """
    Retrieves the most recent research brief from Redis cache or the database
    without triggering a full multi-agent pipeline run.
    """
    ticker = ticker.upper().strip()
    
    # 1. Check Cache
    cached = cache_manager.get(ticker)
    if cached and "final_report" in cached:
        return ResearchResponse(
            ticker=ticker,
            company_name=cached.get("raw_data", {}).get("stock_data", {}).get("short_name", ticker),
            summary=cached["final_report"][:300] + "...",
            final_report=cached["final_report"],
            telemetry=cached.get("telemetry", {"cache": "HIT"}),
            raw_data=cached.get("raw_data", {})
        )
        
    # 2. Check Database
    db = SessionLocal()
    brief = db.query(ResearchBrief).filter_by(ticker=ticker).order_by(ResearchBrief.created_at.desc()).first()
    db.close()
    
    if brief:
        return ResearchResponse(
            ticker=ticker,
            company_name=brief.company_name,
            summary=brief.summary,
            final_report=brief.full_report,
            telemetry={"cache": "DATABASE_FETCH", "source": "PostgreSQL/SQLite"},
            raw_data={}
        )
        
    raise HTTPException(status_code=404, detail=f"No existing research found for ticker {ticker}. Please generate a new brief via POST /research.")

@app.post("/ask", response_model=AskResponse, tags=["Conversational Q&A"])
def ask_followup(request: AskRequest):
    """
    Answers follow-up conversational questions about a company using previous research context.
    """
    ticker = request.ticker.upper().strip()
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    # Retrieve report context
    report_context = ""
    cached = cache_manager.get(ticker)
    if cached and "final_report" in cached:
        report_context = cached["final_report"]
    else:
        db = SessionLocal()
        brief = db.query(ResearchBrief).filter_by(ticker=ticker).order_by(ResearchBrief.created_at.desc()).first()
        db.close()
        if brief:
            report_context = brief.full_report
            
    # Prepare chat messages
    system_prompt = (
        f"You are a Senior Wall Street Equity Research Analyst answering follow-up questions about {ticker}. "
        "Use the provided investment brief context to answer clearly, accurately, and concisely. "
        "If the information is not in the context, state that clearly based on general financial principles."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    if report_context:
        messages.append({"role": "user", "content": f"Here is the finalized research report for context:\n\n{report_context}"})
        messages.append({"role": "assistant", "content": f"Understood. I am ready to answer any questions regarding the {ticker} research brief."})
        
    for msg in request.chat_history:
        messages.append(msg)
        
    messages.append({"role": "user", "content": request.question})
    
    try:
        answer = call_llm_chat(messages=messages)
        
        # Save query to database
        try:
            db = SessionLocal()
            q = Query(ticker=ticker, question=request.question, answer=answer)
            db.add(q)
            db.commit()
            db.close()
        except Exception:
            pass
            
        return AskResponse(
            ticker=ticker,
            question=request.question,
            answer=answer
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent.api.main:app", host="0.0.0.0", port=8000, reload=True)

