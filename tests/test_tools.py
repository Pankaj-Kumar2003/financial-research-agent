import unittest
from unittest.mock import patch, MagicMock
from agent.tools.stock import get_stock_data
from agent.tools.news import get_company_news
from agent.tools.sec import get_sec_filings, get_cik_by_ticker, extract_10k_items

class TestTools(unittest.TestCase):
    def test_stock_data_structure(self):
        data = get_stock_data("AAPL")
        self.assertIsInstance(data, dict)
        if "ticker" in data:
            self.assertEqual(data["ticker"], "AAPL")

    def test_news_structure(self):
        news = get_company_news("AAPL")
        self.assertIsInstance(news, list)
        self.assertGreater(len(news), 0)

    def test_sec_cik_lookup(self):
        cik = get_cik_by_ticker("AAPL")
        self.assertIsNotNone(cik)
        self.assertEqual(len(cik), 10)

    def test_sec_structure(self):
        filings = get_sec_filings("AAPL")
        self.assertIsInstance(filings, list)
        self.assertGreater(len(filings), 0)
        self.assertIn("form", filings[0])

    def test_sec_extractor(self):
        # A mock HTML to test regex extraction logic
        mock_html = '''
        ITEM 1A. RISK FACTORS
        Here are some fake risk factors about our business.
        We face competition.
        ITEM 1B. UNRESOLVED STAFF COMMENTS
        None.
        ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
        Our financial condition is okay.
        ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES
        Market risk is present.
        '''
        results = extract_10k_items(mock_html)
        self.assertIn("Here are some fake risk factors", results["item_1a"])
        self.assertIn("Our financial condition is okay.", results["item_7"])

    @patch('agent.tools.chart.yf.Ticker')
    @patch('agent.tools.chart.plt.savefig')
    def test_generate_price_chart(self, mock_savefig, mock_ticker):
        from unittest.mock import MagicMock
        import pandas as pd
        mock_df = pd.DataFrame({'Close': [100, 105, 110]})
        mock_df.index = pd.date_range("2024-01-01", periods=3)
        mock_stock = MagicMock()
        mock_stock.history.return_value = mock_df
        mock_ticker.return_value = mock_stock
        
        from agent.tools.chart import generate_price_chart
        path = generate_price_chart("AAPL")
        self.assertTrue(path.endswith("AAPL_chart.png"))
        mock_savefig.assert_called_once()

if __name__ == "__main__":
    unittest.main()

