import json
from typing import Dict, Any
from agent.core.base_agent import BaseAgent
from agent.core.state import ResearchState
from agent.llm import call_llm_rest

class FinancialAnalystAgent(BaseAgent):
    """
    Agent responsible for deep-dive quantitative valuation and MD&A review.
    """
    
    @property
    def name(self) -> str:
        return "FinancialAnalystAgent"
        
    @property
    def role(self) -> str:
        return "Analyzes valuation multiples, capital structure, profitability, and 10-K MD&A trends."

    def run(self, state: ResearchState) -> ResearchState:
        print(f"[{self.name}] Initiating financial analysis for {state.ticker}...")
        
        stock_data = state.raw_data.get("stock_data", {})
        sec_insights = state.raw_data.get("sec_insights", {})
        item_7_mda = sec_insights.get("item_7", "No MD&A available.")
        
        system_instruction = (
            "You are a senior fundamental equity analyst at a top-tier investment bank. "
            "Your job is to write a highly professional, dense, and objective financial analysis section. "
            "Focus on valuation multiples (P/E), balance sheet strength (Debt-to-Equity), cash flow, and management's operating narratives. "
            "Do NOT hallucinate metrics that are not provided. Output strictly the analysis in markdown format under the heading '## Financial Analysis'."
        )
        
        prompt = (
            f"Analyze the financial standing of {state.ticker} based on the following raw data:\n\n"
            f"--- FUNDAMENTAL METRICS ---\n{json.dumps(stock_data, indent=2)}\n\n"
            f"--- 10-K ITEM 7 (MD&A) EXCERPT ---\n{item_7_mda}\n\n"
            "Write the '## Financial Analysis' section. Provide insights on valuation premiums/discounts, "
            "margin health, capital structure, and how management explains current operational performance."
        )
        
        try:
            analysis = call_llm_rest(prompt=prompt, system_instruction=system_instruction)
            state.agent_outputs["financial_analysis"] = analysis
            print(f"[{self.name}]   -> Financial analysis generated successfully.")
        except Exception as e:
            msg = f"Financial analysis failed: {e}"
            print(f"[{self.name}] [!] {msg}")
            state.agent_outputs["financial_analysis"] = f"## Financial Analysis\n\nFailed to generate analysis due to LLM error: {e}"
            state.errors.append(msg)
            
        return state

