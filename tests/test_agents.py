import unittest
from agent.core.state import ResearchState
from agent.agents.data_agent import DataGatheringAgent

from agent.agents.financial_agent import FinancialAnalystAgent
from agent.agents.risk_agent import RiskAndNewsAgent
from agent.agents.coordinator_agent import SynthesisCoordinatorAgent
from unittest.mock import patch

class TestAgents(unittest.TestCase):
    def test_research_state_initialization(self):
        state = ResearchState(ticker="AAPL")
        self.assertEqual(state.ticker, "AAPL")
        self.assertIsInstance(state.raw_data, dict)
        self.assertEqual(len(state.raw_data), 0)
        self.assertEqual(len(state.errors), 0)

    def test_data_gathering_agent_execution(self):
        state = ResearchState(ticker="AAPL")
        agent = DataGatheringAgent()
        
        self.assertEqual(agent.name, "DataGatheringAgent")
        new_state = agent.run(state)
        
        self.assertIn("stock_data", new_state.raw_data)
        self.assertIn("news_data", new_state.raw_data)
        self.assertIn("sec_data", new_state.raw_data)
        self.assertIn("sec_insights", new_state.raw_data)
        
        self.assertGreater(len(new_state.raw_data["news_data"]), 0)
        self.assertGreater(len(new_state.raw_data["sec_data"]), 0)

    @patch('agent.agents.financial_agent.call_llm_rest')
    def test_financial_analyst_agent(self, mock_llm):
        mock_llm.return_value = "## Financial Analysis\n\nMocked financial analysis."
        state = ResearchState(ticker="AAPL")
        state.raw_data = {"stock_data": {"price": 150}, "sec_insights": {"item_7": "Good margins."}}
        
        agent = FinancialAnalystAgent()
        new_state = agent.run(state)
        
        self.assertIn("financial_analysis", new_state.agent_outputs)
        self.assertIn("Mocked financial analysis", new_state.agent_outputs["financial_analysis"])

    @patch('agent.agents.risk_agent.call_llm_rest')
    def test_risk_and_news_agent(self, mock_llm):
        mock_llm.return_value = "## Risk and Sentiment Analysis\n\nMocked risk analysis."
        state = ResearchState(ticker="AAPL")
        state.raw_data = {"news_data": [{"title": "Bad news"}], "sec_insights": {"item_1a": "High risk."}}
        
        agent = RiskAndNewsAgent()
        new_state = agent.run(state)
        
        self.assertIn("risk_analysis", new_state.agent_outputs)
        self.assertIn("Mocked risk analysis", new_state.agent_outputs["risk_analysis"])

    @patch('agent.agents.coordinator_agent.call_llm_rest')
    def test_synthesis_coordinator_agent(self, mock_llm):
        mock_llm.return_value = "## Executive Summary\n\nMocked final report."
        state = ResearchState(ticker="AAPL")
        state.agent_outputs = {
            "financial_analysis": "## Financial Analysis\nData.",
            "risk_analysis": "## Risk Analysis\nData."
        }
        
        agent = SynthesisCoordinatorAgent()
        new_state = agent.run(state)
        
        self.assertIsNotNone(new_state.final_report)
        self.assertIn("Mocked final report", new_state.final_report)

    @patch('agent.agents.coordinator_agent.call_llm_rest')
    def test_synthesis_coordinator_with_user_feedback(self, mock_llm):
        mock_llm.return_value = "## Executive Summary\n\nMocked custom report."
        state = ResearchState(ticker="AAPL")
        state.agent_outputs = {
            "financial_analysis": "## Financial Analysis\nData.",
            "risk_analysis": "## Risk Analysis\nData."
        }
        state.user_feedback = "Please write this purely in Spanish."
        
        agent = SynthesisCoordinatorAgent()
        new_state = agent.run(state)
        
        # Verify the LLM was called with the user feedback in the prompt
        call_args = mock_llm.call_args[1]
        self.assertIn("Please write this purely in Spanish.", call_args["prompt"])
        self.assertIsNotNone(new_state.final_report)

    @patch('agent.agents.comparison_agent.call_llm_rest')
    def test_comparison_analyst_agent(self, mock_llm):
        mock_llm.return_value = "## ⚔️ Head-to-Head Valuation Matrix\nMocked comparison."
        
        state_a = ResearchState(ticker="NVDA")
        state_a.agent_outputs = {"financial_analysis": "Great financials."}
        
        state_b = ResearchState(ticker="AMD")
        state_b.agent_outputs = {"financial_analysis": "Good financials."}
        
        from agent.agents.comparison_agent import ComparisonAnalystAgent
        agent = ComparisonAnalystAgent()
        report = agent.compare(state_a, state_b)
        
        self.assertIn("Head-to-Head Valuation Matrix", report)
        self.assertIn("Mocked comparison", report)

    @patch('agent.agents.portfolio_agent.call_llm_rest')
    def test_portfolio_risk_agent(self, mock_llm):
        mock_llm.return_value = "## 💼 Portfolio Health Summary\nMocked portfolio risk."
        
        state_a = ResearchState(ticker="AAPL")
        state_b = ResearchState(ticker="MSFT")
        
        from agent.agents.portfolio_agent import PortfolioRiskAgent
        agent = PortfolioRiskAgent()
        report = agent.analyze([state_a, state_b])
        
        self.assertIn("Portfolio Health Summary", report)
        mock_llm.assert_called_once()

if __name__ == "__main__":
    unittest.main()

