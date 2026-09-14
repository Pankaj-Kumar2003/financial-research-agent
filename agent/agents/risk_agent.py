import json
from typing import Dict, Any
from agent.core.base_agent import BaseAgent
from agent.core.state import ResearchState
from agent.llm import call_llm_rest

class RiskAndNewsAgent(BaseAgent):
    """
    Agent responsible for analyzing risk factors (SEC Item 1A) and recent market sentiment (News).
    """
    
    @property
    def name(self) -> str:
        return "RiskAndNewsAgent"
        
    @property
    def role(self) -> str:
        return "Evaluates 10-K Risk Factors (Item 1A) and recent news sentiment to identify threats."

    def run(self, state: ResearchState) -> ResearchState:
        print(f"[{self.name}] Initiating risk and sentiment analysis for {state.ticker}...")
        
        news_data = state.raw_data.get("news_data", [])
        sec_insights = state.raw_data.get("sec_insights", {})
        item_1a_risk = sec_insights.get("item_1a", "No Risk Factors available.")
        
        system_instruction = (
            "You are a Chief Risk Officer and quantitative market analyst. "
            "Your job is to write a highly professional, objective risk and sentiment analysis section. "
            "Focus on regulatory threats, competitive dynamics, macroeconomic risks, and how recent news impacts the company. "
            "Do NOT hallucinate events. Output strictly the analysis in markdown format under the heading '## Risk and Sentiment Analysis'."
        )
        
        prompt = (
            f"Analyze the risk profile and recent market sentiment for {state.ticker} based on the following raw data:\n\n"
            f"--- RECENT NEWS HEADLINES ---\n{json.dumps(news_data, indent=2)}\n\n"
            f"--- 10-K ITEM 1A (RISK FACTORS) EXCERPT ---\n{item_1a_risk}\n\n"
            "Write the '## Risk and Sentiment Analysis' section. Provide insights on critical SEC-disclosed risks, "
            "and how recent news events either mitigate or exacerbate these risks."
        )
        
        try:
            analysis = call_llm_rest(prompt=prompt, system_instruction=system_instruction)
            state.agent_outputs["risk_analysis"] = analysis
            print(f"[{self.name}]   -> Risk analysis generated successfully.")
        except Exception as e:
            msg = f"Risk analysis failed: {e}"
            print(f"[{self.name}] [!] {msg}")
            state.agent_outputs["risk_analysis"] = f"## Risk and Sentiment Analysis\n\nFailed to generate analysis due to LLM error: {e}"
            state.errors.append(msg)
            
        return state

