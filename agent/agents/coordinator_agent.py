from agent.core.base_agent import BaseAgent
from agent.core.state import ResearchState
from agent.llm import call_llm_rest

class SynthesisCoordinatorAgent(BaseAgent):
    """
    Agent responsible for synthesizing inputs from all sub-agents into a final report.
    """
    
    @property
    def name(self) -> str:
        return "SynthesisCoordinatorAgent"
        
    @property
    def role(self) -> str:
        return "Chief Investment Officer merging financial and risk analyses into a final report."

    def run(self, state: ResearchState) -> ResearchState:
        print(f"[{self.name}] Initiating final synthesis for {state.ticker}...")
        
        financial_analysis = state.agent_outputs.get("financial_analysis", "No financial analysis provided.")
        risk_analysis = state.agent_outputs.get("risk_analysis", "No risk analysis provided.")
        
        system_instruction = (
            "You are a Chief Investment Officer and Managing Editor. "
            "Your job is to synthesize specialized financial and risk analyses into a cohesive, professional 6-section Investment Brief. "
            "Ensure the tone is objective, authoritative, and flows logically. "
            "Output the final markdown report directly, without any conversational preamble."
        )
        
        feedback_block = ""
        if state.user_feedback:
            feedback_block = (
                f"\n--- CRITICAL USER FEEDBACK / INSTRUCTIONS ---\n"
                f"The user has explicitly requested the following focus/constraint: {state.user_feedback}\n"
                f"You MUST ensure the final report directly addresses this feedback and aligns with their intent.\n"
            )
        
        prompt = (
            f"Please synthesize the following analytical reports for {state.ticker} into a final 6-section Investment Brief.\n\n"
            f"--- FINANCIAL ANALYST REPORT ---\n{financial_analysis}\n\n"
            f"--- RISK & NEWS ANALYST REPORT ---\n{risk_analysis}\n"
            f"{feedback_block}\n"
            f"Format your output strictly with these exact markdown headers:\n\n"
            f"## Executive Summary\n<Write a high-level summary of the thesis and business model>\n\n"
            f"## Financial Health\n<Integrate the Financial Analyst Report here>\n\n"
            f"## Recent Developments\n<Highlight key events based on news or recent filings>\n\n"
            f"## SEC Filing Highlights\n<Provide context on recent regulatory filings>\n\n"
            f"## Risk Factors\n<Integrate the Risk & News Analyst Report here>\n\n"
            f"## Outlook\n<Synthesize a forward-looking conclusion balancing bull and bear factors>\n"
        )
        
        try:
            final_report = call_llm_rest(prompt=prompt, system_instruction=system_instruction)
            # Prepend the main title if it's not already there
            if not final_report.startswith("# Investment Brief"):
                final_report = f"# Investment Brief: {state.ticker}\n\n{final_report}"
            
            state.final_report = final_report
            print(f"[{self.name}]   -> Final report synthesized successfully.")
        except Exception as e:
            msg = f"Report synthesis failed: {e}"
            print(f"[{self.name}] [!] {msg}")
            state.final_report = f"# Investment Brief: {state.ticker}\n\nFailed to generate final report due to LLM error: {e}"
            state.errors.append(msg)
            
        return state

