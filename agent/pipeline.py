import os
from agent.core.state import ResearchState
from agent.agents.data_agent import DataGatheringAgent
from agent.agents.financial_agent import FinancialAnalystAgent
from agent.agents.risk_agent import RiskAndNewsAgent
from agent.agents.coordinator_agent import SynthesisCoordinatorAgent
from agent.db.cache import cache_manager
from agent.db.database import init_db, SessionLocal
from agent.db.models import ResearchBrief, Source, EvaluationRun
from agent.observability.tracker import ObservabilityTracker

# Initialize database tables
init_db()

def save_report(ticker: str, content: str, output_dir: str = "reports") -> str:
    """Save generated investment brief to a persistent markdown file."""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{ticker}_investment_brief.md")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
            
    return file_path

def run_multi_agent_pipeline(ticker: str, interactive_feedback: bool = False, use_cache: bool = True) -> ResearchState:
    """
    Day 16 Multi-Agent Pipeline Orchestrator.
    Passes a ResearchState through Data -> Financial Analyst -> Risk Analyst -> Coordinator.
    Features Redis Caching, Observability Telemetry, and SQLAlchemy Database Persistence.
    """
    ticker = ticker.upper().strip()
    
    # 1. Check Redis/Memory Cache First
    if use_cache:
        cached_payload = cache_manager.get(ticker)
        if cached_payload and "final_report" in cached_payload:
            state = ResearchState(ticker=ticker)
            state.final_report = cached_payload["final_report"]
            state.raw_data = cached_payload.get("raw_data", {})
            state.agent_outputs = cached_payload.get("agent_outputs", {})
            state.raw_data["telemetry"] = cached_payload.get("telemetry", {"cache": "HIT", "total_latency_seconds": 0.005, "total_tokens": 0, "estimated_cost_usd": 0.0})
            print(f"[Pipeline] Cache HIT for {ticker}. Returning cached brief.")
            return state

    print("\n" + "="*60)
    print(f"[*] Starting Multi-Agent Financial Research for: {ticker}")
    print("="*60 + "\n")
    
    # Initialize Observability Tracker
    with ObservabilityTracker(ticker) as tracker:
        # Initialize the shared blackboard
        state = ResearchState(ticker=ticker)
        
        # Define our agent team sequence
        agents = [
            DataGatheringAgent(),
            FinancialAnalystAgent(),
            RiskAndNewsAgent(),
            SynthesisCoordinatorAgent()
        ]
        
        # Execute the graph
        for agent in agents:
            # HITL Interruption Check
            if interactive_feedback and agent.name == "SynthesisCoordinatorAgent":
                print("\n" + "="*60)
                print("   [HUMAN-IN-THE-LOOP CHECKPOINT]")
                print("   The Data, Financial, and Risk agents have completed their analysis.")
                print("="*60)
                user_fb = input("[?] Any custom instructions for the final report?\n"
                                "    (e.g., 'Emphasize AI risks', 'Make the tone extremely bearish')\n"
                                "    [Press ENTER to skip and auto-generate]: ").strip()
                if user_fb:
                    state.user_feedback = user_fb
                    print(f"[+] Custom feedback applied: '{user_fb}'")
                else:
                    print("[+] Proceeding with autonomous synthesis.")
                print("-" * 40)

            t0 = os.times().elapsed if hasattr(os, 'times') else 0
            state = agent.run(state)
            print("-" * 40)

        # Telemetry calculations
        telemetry = tracker.to_dict()
        telemetry["cache"] = "MISS"
        state.raw_data["telemetry"] = telemetry

    # Format and save final report
    print("\n" + "="*60)
    print(f"        INVESTMENT BRIEF: {ticker}")
    print("="*60 + "\n")
    
    if state.final_report:
        print(state.final_report)
        report_file = save_report(ticker, state.final_report)
        print(f"\n[+] Report successfully saved to: {report_file}\n")
        
        # Persist to Database via SQLAlchemy
        try:
            db = SessionLocal()
            brief = ResearchBrief(
                ticker=ticker,
                company_name=state.raw_data.get("stock_data", {}).get("short_name", ticker),
                full_report=state.final_report,
                summary=state.final_report[:300] + "..."
            )
            db.add(brief)
            db.flush()
            
            # Persist Telemetry Run
            eval_run = EvaluationRun(
                ticker=ticker,
                total_latency_seconds=telemetry["total_latency_seconds"],
                llm_latency_seconds=telemetry["llm_latency_seconds"],
                tool_latency_seconds=telemetry["tool_latency_seconds"],
                total_tokens=telemetry["total_tokens"],
                estimated_cost_usd=telemetry["estimated_cost_usd"],
                error_count=len(state.errors)
            )
            db.add(eval_run)
            db.commit()
            db.close()
            print(f"[Database] Saved ResearchBrief and EvaluationRun to SQLAlchemy database.")
        except Exception as db_err:
            print(f"[Database] [!] DB save failed: {db_err}")
            
        # Cache Result in Redis / Memory Cache
        cache_payload = {
            "final_report": state.final_report,
            "raw_data": state.raw_data,
            "agent_outputs": state.agent_outputs,
            "telemetry": telemetry
        }
        cache_manager.set(ticker, cache_payload)
    else:
        print("[!] Pipeline failed to produce a final report.")
        
    if state.errors:
        print(f"[!] Pipeline finished with {len(state.errors)} non-fatal errors.")
        
    return state

def run_comparison_pipeline(ticker_a: str, ticker_b: str, interactive_feedback: bool = False) -> tuple[str, str]:
    """
    Day 14 Comparative Pipeline.
    Runs the full multi-agent pipeline for two stocks, then compares them side-by-side.
    Returns (markdown_report, chart_path)
    """
    ticker_a = ticker_a.upper().strip()
    ticker_b = ticker_b.upper().strip()
    
    print("\n" + "="*80)
    print(f"[*] Starting Dual-Ticker Comparative Analysis: {ticker_a} vs {ticker_b}")
    print("="*80 + "\n")
    
    # 1. Run pipeline for Ticker A
    state_a = run_multi_agent_pipeline(ticker_a, interactive_feedback=interactive_feedback)
    
    # 2. Run pipeline for Ticker B
    state_b = run_multi_agent_pipeline(ticker_b, interactive_feedback=interactive_feedback)
    
    # 3. Run Comparison Agent
    print("\n" + "="*80)
    print(f"[*] Running Comparison Analyst Agent...")
    print("="*80 + "\n")
    
    from agent.agents.comparison_agent import ComparisonAnalystAgent
    comp_agent = ComparisonAnalystAgent()
    comparison_report = comp_agent.compare(state_a, state_b)
    
    # Generate Comparison Chart
    from agent.tools.chart import generate_comparison_chart
    chart_path = generate_comparison_chart(ticker_a, ticker_b)
    
    # 4. Save and return report
    report_file = save_report(f"{ticker_a}_vs_{ticker_b}_comparison", comparison_report)
    print(f"\n[+] Comparative Report successfully saved to: {report_file}\n")
    
    return comparison_report, chart_path

def run_portfolio_pipeline(tickers: list[str]) -> tuple[str, str]:
    """
    Day 16 Portfolio Pipeline.
    Runs the full multi-agent pipeline for multiple stocks concurrently, 
    then assesses aggregate portfolio risk.
    """
    cleaned_tickers = [t.upper().strip() for t in tickers if t.strip()]
    
    print("\n" + "="*80)
    print(f"[*] Starting Batch Portfolio Analysis: {', '.join(cleaned_tickers)}")
    print("="*80 + "\n")
    
    import concurrent.futures
    states = []
    
    # 1. Run pipelines concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cleaned_tickers)) as executor:
        futures = {executor.submit(run_multi_agent_pipeline, t, False): t for t in cleaned_tickers}
        for future in concurrent.futures.as_completed(futures):
            try:
                states.append(future.result())
            except Exception as e:
                print(f"[!] Pipeline failed for {futures[future]}: {e}")
                
    # 2. Generate Sector Chart
    from agent.tools.chart import generate_portfolio_sector_chart
    chart_path = generate_portfolio_sector_chart(cleaned_tickers)
    
    # 3. Run Portfolio Agent
    print("\n" + "="*80)
    print(f"[*] Running Portfolio Risk Agent...")
    print("="*80 + "\n")
    
    from agent.agents.portfolio_agent import PortfolioRiskAgent
    port_agent = PortfolioRiskAgent()
    portfolio_report = port_agent.analyze(states)
    
    # 4. Save and return
    report_file = save_report("portfolio_risk_report", portfolio_report)
    print(f"\n[+] Portfolio Report successfully saved to: {report_file}\n")
    
    return portfolio_report, chart_path

if __name__ == "__main__":
    import sys
    test_ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    run_multi_agent_pipeline(test_ticker)
