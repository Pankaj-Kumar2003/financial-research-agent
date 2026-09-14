import unittest
from unittest.mock import patch
from agent.evaluation.judge import GroundingJudge

class TestGroundingJudge(unittest.TestCase):

    def test_empty_report_handling(self):
        judge = GroundingJudge()
        result = judge.evaluate("", {})
        self.assertEqual(result["total_claims"], 0)
        self.assertEqual(result["grounding_score_percent"], 100.0)

    @patch('agent.evaluation.judge.call_llm_chat')
    def test_judge_parses_supported_claims(self, mock_llm):
        mock_llm.return_value = """{
            "claims": [
                {
                    "claim": "Apple's P/E ratio is 32.5",
                    "verdict": "SUPPORTED",
                    "source_reference": "yfinance P/E metric: 32.5",
                    "reasoning": "Direct match"
                },
                {
                    "claim": "Supply chain risk in APAC",
                    "verdict": "SUPPORTED",
                    "source_reference": "Item 1A mentions Asian supplier dependencies",
                    "reasoning": "Extracted from 10-K"
                }
            ],
            "total_claims": 2,
            "supported_count": 2,
            "inference_count": 0,
            "unsupported_count": 0,
            "grounding_score_percent": 100.0
        }"""

        judge = GroundingJudge()
        res = judge.evaluate("Apple report", {"stock_data": {"pe_ratio": 32.5}})
        self.assertEqual(res["total_claims"], 2)
        self.assertEqual(res["supported_count"], 2)
        self.assertEqual(res["grounding_score_percent"], 100.0)

if __name__ == "__main__":
    unittest.main()

