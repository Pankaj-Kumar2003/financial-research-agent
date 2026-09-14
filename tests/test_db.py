import unittest
from agent.db.cache import cache_manager
from agent.db.database import SessionLocal, init_db
from agent.db.models import ResearchBrief, EvaluationRun
from agent.observability.tracker import ObservabilityTracker

class TestDay16Backend(unittest.TestCase):
    def setUp(self):
        init_db()
        
    def test_cache_set_and_get(self):
        ticker = "TEST_TICKER"
        data = {"final_report": "Mock brief for caching."}
        
        # Test Cache Set
        set_res = cache_manager.set(ticker, data, ttl=10)
        self.assertTrue(set_res)
        
        # Test Cache Get (Hit)
        cached = cache_manager.get(ticker)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["final_report"], "Mock brief for caching.")
        
        # Test Invalidate
        cache_manager.invalidate(ticker)
        self.assertIsNone(cache_manager.get(ticker))

    def test_observability_tracker(self):
        with ObservabilityTracker("AAPL") as tracker:
            tracker.log_llm_call(prompt="Analyze AAPL financials", response="AAPL has high cash flow.", latency=1.2)
            tracker.log_tool_call("get_stock_data", latency=0.5, docs_retrieved=1, success=True)
            
        metrics = tracker.to_dict()
        self.assertEqual(metrics["ticker"], "AAPL")
        self.assertGreater(metrics["total_tokens"], 0)
        self.assertGreater(metrics["estimated_cost_usd"], 0)
        self.assertAlmostEqual(metrics["llm_latency_seconds"], 1.2)

    def test_sqlalchemy_persistence(self):
        db = SessionLocal()
        brief = ResearchBrief(
            ticker="MOCK_DB",
            company_name="Mock Company",
            full_report="Full report string",
            summary="Summary string"
        )
        db.add(brief)
        db.commit()
        
        fetched = db.query(ResearchBrief).filter_by(ticker="MOCK_DB").first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.company_name, "Mock Company")
        
        db.delete(fetched)
        db.commit()
        db.close()

if __name__ == "__main__":
    unittest.main()

