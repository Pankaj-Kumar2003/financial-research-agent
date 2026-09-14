import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from agent.api.main import app
from agent.core.state import ResearchState

client = TestClient(app)

class TestFastAPIEndpoints(unittest.TestCase):
    
    def test_health_check(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("database", data)
        self.assertIn("cache", data)

    @patch('agent.api.main.run_multi_agent_pipeline')
    def test_post_research(self, mock_pipeline):
        # Mock the pipeline response
        mock_state = ResearchState(ticker="NVDA")
        mock_state.final_report = "## Investment Brief: NVDA\nStrong GPU demand."
        mock_state.raw_data = {"stock_data": {"short_name": "NVIDIA Corp"}, "telemetry": {"cache": "MISS"}}
        mock_pipeline.return_value = mock_state
        
        response = client.post("/research", json={"ticker": "NVDA", "use_cache": False})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ticker"], "NVDA")
        self.assertEqual(data["company_name"], "NVIDIA Corp")
        self.assertIn("Strong GPU demand", data["final_report"])

    @patch('agent.api.main.call_llm_chat')
    def test_post_ask(self, mock_llm_chat):
        mock_llm_chat.return_value = "NVDA leads the data center market with CUDA moats."
        
        response = client.post("/ask", json={
            "ticker": "NVDA",
            "question": "What is NVDA's competitive moat?",
            "chat_history": []
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ticker"], "NVDA")
        self.assertIn("CUDA moats", data["answer"])

    def test_get_existing_research_not_found(self):
        # Random non-existent ticker
        response = client.get("/research/NON_EXISTENT_TICKER_XYZ")
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()

