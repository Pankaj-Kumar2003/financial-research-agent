# 📈 Autonomous Multi-Agent Financial Research Assistant

An institutional-grade, multi-agent financial research and equity analysis platform built in pure Python. The system orchestrates specialized autonomous AI agents to ingest raw financial data, analyze SEC 10-K filings, evaluate market sentiment, and generate actionable investment briefs with technical charts and portfolio risk modeling.

---

## 🌟 Key Architecture & Features

### 1. Multi-Agent Blackboard Pattern

The platform coordinates specialized cognitive agents using a shared Pydantic `ResearchState` blackboard:

- **`DataGatheringAgent`**: Concurrently fetches real-time Yahoo Finance metrics, NewsAPI headlines, SEC EDGAR 10-K filings (Item 1A Risk Factors & Item 7 MD&A), and technical moving averages (`SMA-50`, `SMA-200`).
- **`FinancialAnalystAgent`**: Evaluates quantitative fundamentals, valuation multiples (P/E, EV/EBITDA), revenue growth, and debt health.
- **`RiskAndNewsAgent`**: Dissects qualitative risks from 10-K regulatory disclosures and performs market sentiment scoring.
- **`SynthesisCoordinatorAgent`**: Synthesizes all agent outputs into an executive Investment Brief with clear Buy/Hold/Sell verdicts.
- **`ComparisonAnalystAgent`**: Conducts head-to-head relative valuation and competitive moat comparisons between two stocks.
- **`PortfolioRiskAgent`**: Scans multi-stock portfolios concurrently to detect systemic overlaps and sector concentration.

### 2. Human-in-the-Loop (HITL) Steering

Allows users to inject custom steering instructions (e.g., _"Focus heavily on AI competition"_ or _"Analyze from a conservative value perspective"_) before the final investment brief is drafted.

### 3. Conversational Memory & Follow-up Q&A

Maintains full session context, allowing investors to ask follow-up questions about the generated report (e.g., _"What were the specific risks regarding Taiwan manufacturing?"_).

### 4. Interactive Web Dashboard

A modern Streamlit UI featuring:

- **Executive KPI Tiles**: Live Glanceable metrics (Price, Market Cap, P/E, Debt/Equity).
- **Technical Visualizations**: Matplotlib-rendered 1-year historical price charts with moving averages and asset allocation pie charts.
- **3 Dedicated Tabs**: Single Stock Research, Stock vs. Stock Comparison, and Batch Portfolio Risk Scanner.
- **One-Click Export**: Instant `.md` report download functionality.

---

## 🚀 Quickstart Guide

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/your-username/financial-research-agent.git
cd financial-research-agent
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example configuration and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

- `GROQ_API_KEY`: [Get a free Groq API key](https://console.groq.com/)
- `NEWS_API_KEY`: [Get a free NewsAPI key](https://newsapi.org/)
- `USER_AGENT`: `YourName your_email@domain.com` (Required by SEC EDGAR)

### 3. Launch the Application

#### Streamlit Web Dashboard (Recommended):

```bash
python -m streamlit run app.py
```

#### Terminal Interactive CLI:

```bash
python -m agent.cli
```

#### Run Automated Test Suite:

```bash
python -m unittest discover tests
```

---

## 📁 Repository Structure

```
├── agent/
│   ├── agents/
│   │   ├── base_agent.py          # Abstract Base Agent Class
│   │   ├── data_agent.py          # Parallel Data Ingestion Agent
│   │   ├── financial_agent.py     # Quantitative Financial Analyst Agent
│   │   ├── risk_agent.py          # Qualitative Risk & News Agent
│   │   ├── coordinator_agent.py   # Synthesis & Coordinator Agent
│   │   ├── comparison_agent.py    # Head-to-Head Comparative Agent
│   │   └── portfolio_agent.py     # Batch Portfolio Risk Agent
│   ├── core/
│   │   └── state.py               # Shared Pydantic Blackboard State
│   ├── tools/
│   │   ├── stock.py               # Yahoo Finance Integration
│   │   ├── news.py                # NewsAPI & News Ingestion
│   │   ├── sec.py                 # SEC EDGAR 10-K Scraper & Parser
│   │   └── chart.py               # Matplotlib Technical Charting Engine
│   ├── config.py                  # Environment & Settings
│   ├── llm.py                     # Groq/OpenRouter REST Client with 429 Backoff
│   ├── pipeline.py                # Multi-Agent Workflow Orchestrator
│   └── cli.py                     # Interactive Terminal Interface
├── tests/
│   ├── test_tools.py              # Data Tools Unit Tests
│   ├── test_agents.py             # Agent Logic & Prompt Unit Tests
│   └── test_pipeline.py           # Pipeline Integration Tests
├── reports/                       # Auto-saved Markdown briefs and PNG charts
├── app.py                         # Full Streamlit Web Application
├── requirements.txt               # Pinned Project Dependencies
├── .env.example                   # Environment Template
└── README.md                      # Project Documentation
```
