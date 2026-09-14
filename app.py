import streamlit as st
import os
import sys
from agent.core.state import ResearchState
from agent.agents.data_agent import DataGatheringAgent
from agent.agents.financial_agent import FinancialAnalystAgent
from agent.agents.risk_agent import RiskAndNewsAgent
from agent.agents.coordinator_agent import SynthesisCoordinatorAgent
from agent.llm import call_llm_chat

# Page Config
st.set_page_config(
    page_title="Multi-Agent Financial Research",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "research_state" not in st.session_state:
    st.session_state.research_state = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR: Conversational Assistant ---
with st.sidebar:
    st.title("💬 Research Assistant")
    st.caption("Ask follow-up questions about the generated report.")
    
    if st.session_state.research_state and st.session_state.research_state.final_report:
        # Display existing chat messages
        for message in st.session_state.chat_history:
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # User input for follow-up questions
        if prompt := st.chat_input("Ask a question about this report..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Prepare messages for LLM
            chat_messages = [{"role": "system", "content": f"You are a helpful Financial Research Assistant. Context report:\n{st.session_state.research_state.final_report}"}]
            chat_messages.extend(st.session_state.chat_history)
            chat_messages.append({"role": "user", "content": prompt})
            
            # Call LLM
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    try:
                        response = call_llm_chat(chat_messages)
                        st.markdown(response)
                        # Store in state
                        st.session_state.chat_history.append({"role": "user", "content": prompt})
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.info("👈 Generate an investment brief to unlock the interactive chat assistant!")

# --- MAIN SCREEN ---
st.markdown('<div class="main-header">📈 Multi-Agent Financial Research Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Powered by EDGAR SEC filings, Yahoo Finance, Groq, and an Autonomous Team of AI Agents</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Single Stock Research", "⚔️ Stock vs. Stock Comparison", "💼 Portfolio Risk Scanner"])

with tab1:
    # Search Controls
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_input = st.text_input("Enter Stock Ticker Symbol:", value="NVDA", max_chars=10).upper().strip()
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("🚀 Generate Brief", use_container_width=True)

    # HITL Custom Steering Input
    st.markdown("---")
    with st.expander("⚙️ Optional: Human-in-the-Loop Steering (Custom Instructions)"):
        user_feedback_input = st.text_area(
            "Direct the Synthesis Agent before report generation:",
            placeholder="e.g. 'Focus heavily on GPU competition from AMD', or 'Emphasize debt solvency and valuation discounts'",
            help="The Synthesis Coordinator Agent will prioritize your custom steering instructions when compiling the final report."
        )

    # Execution Graph
    if generate_btn and ticker_input:
        import httpx
        from agent.db.cache import cache_manager

        ticker = ticker_input.upper().strip()
        st.session_state.chat_history = []
        st.session_state.research_state = ResearchState(ticker=ticker)
        
        status_container = st.container()
        
        with status_container:
            st.markdown("### 🤖 Agent Execution Graph")
            
            with st.status(f"Connecting to FastAPI Backend for {ticker}...", expanded=True) as status:
                st.write("• Sending POST request to http://localhost:8000/research")
                
                try:
                    # Make HTTP request to FastAPI backend
                    api_url = os.environ.get("API_URL", "http://localhost:8000")
                    payload = {
                        "ticker": ticker,
                        "user_feedback": user_feedback_input.strip() if user_feedback_input.strip() else None,
                        "use_cache": True
                    }
                    
                    response = httpx.post(
                        f"{api_url}/research", 
                        json=payload,
                        timeout=120.0  # Multi-agent pipelines take time!
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.research_state.final_report = data["final_report"]
                        st.session_state.research_state.raw_data = data.get("raw_data", {})
                        
                        # Fix up missing paths for UI
                        if "telemetry" not in st.session_state.research_state.raw_data:
                            st.session_state.research_state.raw_data["telemetry"] = data.get("telemetry", {})
                            
                        cache_status = data.get("telemetry", {}).get("cache", "MISS")
                        if cache_status == "HIT":
                            status.update(label=f"✅ Loaded {ticker} from Cache!", state="complete", expanded=False)
                            st.success(f"🎯 Cache HIT for {ticker}! Loaded instantly.")
                        else:
                            st.write("• Autonomous agents executed successfully.")
                            status.update(label="✅ Multi-Agent Pipeline Complete", state="complete", expanded=False)
                    else:
                        st.error(f"API Error {response.status_code}: {response.text}")
                        status.update(label="❌ API Error", state="error", expanded=False)
                        
                except (httpx.RequestError, httpx.HTTPError) as e:
                    st.info("FastAPI backend not detected. Running autonomous agents directly in-process...")
                    from agent.agents.data_agent import DataGatheringAgent
                    from agent.agents.financial_agent import FinancialAnalystAgent
                    from agent.agents.risk_agent import RiskAndNewsAgent
                    from agent.agents.coordinator_agent import SynthesisCoordinatorAgent
                    from agent.observability.tracker import ObservabilityTracker

                    if user_feedback_input.strip():
                        st.session_state.research_state.user_feedback = user_feedback_input.strip()

                    with ObservabilityTracker(ticker) as tracker:
                        st.write("• DataGatheringAgent: Gathering Market & SEC filings...")
                        st.session_state.research_state = DataGatheringAgent().run(st.session_state.research_state)
                        st.write("• FinancialAnalystAgent: Computing valuation & ratios...")
                        st.session_state.research_state = FinancialAnalystAgent().run(st.session_state.research_state)
                        st.write("• RiskAndNewsAgent: Evaluating risk factors & sentiment...")
                        st.session_state.research_state = RiskAndNewsAgent().run(st.session_state.research_state)
                        st.write("• SynthesisCoordinatorAgent: Compiling final executive brief...")
                        st.session_state.research_state = SynthesisCoordinatorAgent().run(st.session_state.research_state)

                        telemetry = tracker.to_dict()
                        telemetry["cache"] = "STANDALONE_CLOUD"
                        st.session_state.research_state.raw_data["telemetry"] = telemetry

                    status.update(label="✅ Multi-Agent Pipeline Complete (Cloud In-Process)", state="complete", expanded=False)

    # Display Final Report
    if st.session_state.research_state and st.session_state.research_state.final_report:
        # Display Telemetry Badges
        telemetry = st.session_state.research_state.raw_data.get("telemetry", {})
        if telemetry:
            lat = telemetry.get("total_latency_seconds", 0)
            tok = telemetry.get("total_tokens", 0)
            cost = telemetry.get("estimated_cost_usd", 0.0)
            cache_status = telemetry.get("cache", "MISS")
            badge_color = "green" if cache_status == "HIT" else "blue"
            
            st.caption(
                f"⚡ **Latency**: `{lat}s` | "
                f"🪙 **Tokens**: `{tok:,}` | "
                f"💵 **Est. Cost**: `${cost:.5f}` | "
                f"🎯 **Cache**: `:{badge_color}[{cache_status}]`"
            )
            st.markdown("<br>", unsafe_allow_html=True)
            
        # Display Metrics
        stock_data = st.session_state.research_state.raw_data.get("stock_data", {})
        if stock_data:
            def format_market_cap(val):
                if not val or val == "N/A": return "N/A"
                try:
                    v = float(val)
                    if v >= 1e12: return f"${v/1e12:.2f}T"
                    if v >= 1e9: return f"${v/1e9:.2f}B"
                    if v >= 1e6: return f"${v/1e6:.2f}M"
                    return f"${v:.2f}"
                except:
                    return val
                    
            c1, c2, c3, c4 = st.columns(4)
            price = stock_data.get("current_price", stock_data.get("currentPrice", "N/A"))
            pe = stock_data.get("pe_ratio", stock_data.get("trailingPE", "N/A"))
            mcap = format_market_cap(stock_data.get("market_cap", stock_data.get("marketCap")))
            dte = stock_data.get("debt_to_equity", stock_data.get("debtToEquity", "N/A"))
            
            c1.metric("Current Price", f"${price:.2f}" if isinstance(price, (int, float)) else f"${price}" if price != "N/A" else "N/A")
            c2.metric("Market Cap", mcap)
            c3.metric("Trailing P/E", f"{pe:.2f}x" if isinstance(pe, (int, float)) else pe)
            c4.metric("Debt-to-Equity", f"{dte:.2f}" if isinstance(dte, (int, float)) else dte)
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Display Charts if available
        chart_path = st.session_state.research_state.raw_data.get("chart_path")
        if chart_path and os.path.exists(chart_path):
            st.image(chart_path, width="stretch")
            
        # Display Bonus Day 19 Visuals (Alpha Backtest & Sentiment Meter)
        backtest_path = st.session_state.research_state.raw_data.get("backtest_chart_path")
        sentiment_path = st.session_state.research_state.raw_data.get("sentiment_chart_path")
        
        if (backtest_path and os.path.exists(backtest_path)) or (sentiment_path and os.path.exists(sentiment_path)):
            col_bt, col_sent = st.columns(2)
            with col_bt:
                if backtest_path and os.path.exists(backtest_path):
                    st.image(backtest_path, width="stretch")
            with col_sent:
                if sentiment_path and os.path.exists(sentiment_path):
                    st.image(sentiment_path, width="stretch")
            
        # Save Report to Disk automatically
        from agent.pipeline import save_report
        saved_path = save_report(st.session_state.research_state.ticker, st.session_state.research_state.final_report)
        st.caption(f"💾 Report saved persistently to `{saved_path}`")
        
        # Render Report
        st.markdown(st.session_state.research_state.final_report)
        
        st.markdown("---")
        st.download_button(
            label="📥 Download Investment Brief (.md)",
            data=st.session_state.research_state.final_report,
            file_name=f"{st.session_state.research_state.ticker}_investment_brief.md",
            mime="text/markdown",
            use_container_width=True
        )

with tab2:
    st.markdown("### ⚔️ Comparative Dual-Ticker Analysis")
    st.markdown("Run two autonomous agent pipelines in parallel and synthesize a head-to-head relative valuation matrix.")
    
    colA, colB = st.columns(2)
    with colA:
        ticker_a = st.text_input("Ticker A:", value="NVDA").upper().strip()
    with colB:
        ticker_b = st.text_input("Ticker B:", value="AMD").upper().strip()
        
    comp_btn = st.button("⚔️ Run Comparative Analysis", use_container_width=True)
    
    if comp_btn and ticker_a and ticker_b:
        from agent.pipeline import run_comparison_pipeline
        
        with st.spinner(f"Running dual-agent pipelines for {ticker_a} and {ticker_b}... This may take 60-90 seconds."):
            # We use the pipeline function directly, which prints to stdout, 
            # but we just want the final markdown output here.
            final_comparison_report, chart_path = run_comparison_pipeline(ticker_a, ticker_b, interactive_feedback=False)
            
            st.success("✅ Comparative Analysis Complete!")
            st.markdown("---")
            
            if chart_path and os.path.exists(chart_path):
                st.image(chart_path, width="stretch")
                
            st.markdown(final_comparison_report)
            
            st.markdown("---")
            st.download_button(
                label="📥 Download Comparative Report (.md)",
                data=final_comparison_report,
                file_name=f"{ticker_a}_vs_{ticker_b}_comparison.md",
                mime="text/markdown",
                use_container_width=True
            )

with tab3:
    st.markdown("### 💼 Batch Portfolio Risk Scanner")
    st.markdown("Analyze multiple holdings concurrently to detect systemic overlaps and sector concentration.")
    
    portfolio_input = st.text_input("Enter Portfolio Tickers (comma-separated):", value="AAPL, MSFT, NVDA, GOOGL")
    port_btn = st.button("💼 Analyze Portfolio Risk", use_container_width=True)
    
    if port_btn and portfolio_input:
        tickers = [t.strip() for t in portfolio_input.split(",")]
        
        from agent.pipeline import run_portfolio_pipeline
        with st.spinner(f"Running concurrent agent pipelines for {len(tickers)} stocks..."):
            port_report, port_chart = run_portfolio_pipeline(tickers)
            
            st.success("✅ Portfolio Analysis Complete!")
            st.markdown("---")
            
            if port_chart and os.path.exists(port_chart):
                st.image(port_chart, width=500)
                
            st.markdown(port_report)
            
            st.markdown("---")
            st.download_button(
                label="📥 Download Portfolio Risk Assessment (.md)",
                data=port_report,
                file_name="portfolio_risk_assessment.md",
                mime="text/markdown",
                use_container_width=True
            )

