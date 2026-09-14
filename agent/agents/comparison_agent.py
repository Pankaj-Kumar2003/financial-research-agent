import json
from agent.core.state import ResearchState
from agent.llm import call_llm_rest

class ComparisonAnalystAgent:
    """
    Agent responsible for performing a head-to-head comparison of two analyzed stocks.
    Note: Does not inherit from BaseAgent because it takes two states instead of one.
    """
    
    @property
    def name(self) -> str:
        return "ComparisonAnalystAgent"
        
    @property
    def role(self) -> str:
        return "Relative Value Strategist comparing fundamentals, growth, and risks of two companies."

    def compare(self, state_a: ResearchState, state_b: ResearchState) -> str:
        ticker_a = state_a.ticker
        ticker_b = state_b.ticker
        print(f"[{self.name}] Initiating head-to-head comparison: {ticker_a} vs {ticker_b}...")
        
        # Extract summaries and metrics
        financials_a = state_a.agent_outputs.get("financial_analysis", "No financial data")
        risks_a = state_a.agent_outputs.get("risk_analysis", "No risk data")
        metrics_a = json.dumps(state_a.raw_data.get("stock_data", {}), indent=2)
        
        financials_b = state_b.agent_outputs.get("financial_analysis", "No financial data")
        risks_b = state_b.agent_outputs.get("risk_analysis", "No risk data")
        metrics_b = json.dumps(state_b.raw_data.get("stock_data", {}), indent=2)
        
        system_instruction = (
            "You are a Senior Relative Value Strategist at a top-tier investment bank. "
            "Your job is to compare two competing companies head-to-head based on their fundamentals, risk profiles, and growth strategies. "
            "Output the final comparative report directly in markdown, without conversational preamble."
        )
        
        prompt = (
            f"Perform a head-to-head comparative analysis of {ticker_a} vs {ticker_b}.\n\n"
            f"--- {ticker_a} METRICS & HIGHLIGHTS ---\n{metrics_a}\n{financials_a}\n{risks_a}\n\n"
            f"--- {ticker_b} METRICS & HIGHLIGHTS ---\n{metrics_b}\n{financials_b}\n{risks_b}\n\n"
            f"Format your output strictly with these exact markdown headers:\n\n"
            f"## ⚔️ Head-to-Head Valuation Matrix\n<Provide a markdown table comparing their key metrics side-by-side, followed by brief commentary>\n\n"
            f"## 📈 Growth Strategy & Moat Comparison\n<Compare their strategic advantages and MD&A narratives>\n\n"
            f"## ⚠️ Risk & Exposure Contrast\n<Contrast their respective SEC risk factors and macro vulnerabilities>\n\n"
            f"## 🏆 Final Investment Verdict\n<Conclude with a clear verdict, e.g., which is better for Value vs Growth>\n"
        )
        
        try:
            report = call_llm_rest(prompt=prompt, system_instruction=system_instruction)
            if not report.startswith("#"):
                report = f"# Comparative Analysis: {ticker_a} vs {ticker_b}\n\n{report}"
            print(f"[{self.name}]   -> Comparative report synthesized successfully.")
            return report
        except Exception as e:
            msg = f"Comparison synthesis failed: {e}"
            print(f"[{self.name}] [!] {msg}")
            return f"# Comparative Analysis: {ticker_a} vs {ticker_b}\n\nFailed to generate comparison due to LLM error: {e}"

