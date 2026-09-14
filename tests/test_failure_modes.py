import unittest
from unittest.mock import patch, MagicMock
from agent.core.state import ResearchState
from agent.agents.data_agent import DataGatheringAgent
from agent.agents.financial_agent import FinancialAnalystAgent

class TestFailureModes(unittest.TestCase):
    
    @patch('agent.agents.data_agent.get_stock_data')
    def test_invalid_ticker_handling(self, mock_get_stock):
        # Simulate Yahoo Finance returning None or raising an error
        mock_get_stock.side_effect = Exception("Ticker not found")
        
        state = ResearchState(ticker="INVALID999")
        agent = DataGatheringAgent()
        
        state = agent.run(state)
        self.assertTrue(len(state.errors) > 0)
        self.assertIn("Ticker not found", str(state.errors))

if __name__ == "__main__":
    unittest.main()
