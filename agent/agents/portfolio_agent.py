import json
from agent.core.state import ResearchState
from agent.llm import call_llm_rest
from typing import List

class PortfolioRiskAgent:
    """
    Agent responsible for analyzing a portfolio of stocks (multiple ResearchStates)
    to identify systemic overlaps and aggregate risks.
    """
    
    @property
    def name(self) -> str:
        return "PortfolioRiskAgent"
        
    @property
    def role(self) -> str:
        return "Chief Risk Officer analyzing systemic exposure across a multi-asset portfolio."

    def analyze(self, states: List[ResearchState]) -> str:
        tickers = [s.ticker for s in states]
        print(f"[{self.name}] Initiating batch portfolio analysis for: {', '.join(tickers)}...")
        
        # Compile all data
        portfolio_context = ""
        for s in states:
            stock_data = s.raw_data.get("stock_data", {})
            risks = s.agent_outputs.get("risk_analysis", "No risk data")
            
            # Extract just key metrics to avoid token overflow
            metrics = {
                "Trailing PE": stock_data.get("trailingPE", "N/A"),
                "Market Cap": stock_data.get("marketCap", "N/A"),
                "Debt/Equity": stock_data.get("debtToEquity", "N/A")
            }
            
            portfolio_context += f"--- {s.ticker} ---\n"
            portfolio_context += f"Metrics: {json.dumps(metrics)}\n"
            portfolio_context += f"Risk Highlights:\n{risks}\n\n"
        
        system_instruction = (
            "You are a Chief Risk Officer reviewing a multi-asset equity portfolio. "
            "Your job is to identify systemic correlations (e.g. all stocks rely on TSMC, all are sensitive to rate hikes). "
            "Output the final report directly in markdown, without conversational preamble."
        )
        
        prompt = (
            f"Perform a comprehensive portfolio risk assessment for the following holdings: {', '.join(tickers)}.\n\n"
            f"{portfolio_context}\n"
            f"Format your output strictly with these exact markdown headers:\n\n"
            f"## 💼 Portfolio Health Summary\n<Brief overview of the portfolio's aggregate valuation and risk profile>\n\n"
            f"## 🕸️ Systemic Overlaps & Correlations\n<Identify common risks shared across multiple holdings (e.g. supply chain, regulation)>\n\n"
            f"## 🛡️ Hedging & Diversification Recommendations\n<Suggest sectors or asset classes to add to offset these specific risks>\n"
        )
        
        try:
            report = call_llm_rest(prompt=prompt, system_instruction=system_instruction)
            if not report.startswith("#"):
                report = f"# Portfolio Risk Assessment\n**Holdings:** {', '.join(tickers)}\n\n{report}"
            print(f"[{self.name}]   -> Portfolio report synthesized successfully.")
            return report
        except Exception as e:
            msg = f"Portfolio synthesis failed: {e}"
            print(f"[{self.name}] [!] {msg}")
            return f"# Portfolio Risk Assessment\nFailed to generate report due to LLM error: {e}"

