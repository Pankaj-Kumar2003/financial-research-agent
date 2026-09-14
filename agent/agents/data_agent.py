import concurrent.futures
from typing import Any, Dict
from agent.core.base_agent import BaseAgent
from agent.core.state import ResearchState

from agent.tools.stock import get_stock_data
from agent.tools.news import get_company_news
from agent.tools.sec import get_sec_filings, download_and_clean_html, extract_10k_items
from agent.tools.chart import generate_price_chart, generate_sentiment_gauge
from agent.tools.backtest import generate_market_backtest_chart

class DataGatheringAgent(BaseAgent):
    """
    Agent responsible for concurrently fetching raw data from all external tools.
    """
    
    @property
    def name(self) -> str:
        return "DataGatheringAgent"
        
    @property
    def role(self) -> str:
        return "Fetches live fundamental, news, and SEC data concurrently."

    def run(self, state: ResearchState) -> ResearchState:
        print(f"[{self.name}] Initiating parallel data gathering for {state.ticker}...")
        
        # We will store the results temporarily
        results: Dict[str, Any] = {
            "stock_data": {},
            "news_data": [],
            "sec_data": [],
            "sec_insights": {},
            "chart_path": "",
            "backtest_chart_path": "",
            "sentiment_chart_path": ""
        }
        
        # Execute tools concurrently using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_stock = executor.submit(get_stock_data, state.ticker)
            future_news = executor.submit(get_company_news, state.ticker)
            future_sec = executor.submit(get_sec_filings, state.ticker)
            future_chart = executor.submit(generate_price_chart, state.ticker)
            future_backtest = executor.submit(generate_market_backtest_chart, state.ticker)
            
            try:
                results["stock_data"] = future_stock.result()
                print(f"[{self.name}]   -> Stock data fetched successfully.")
            except Exception as e:
                msg = f"Stock data fetch failed: {e}"
                print(f"[{self.name}] [!] {msg}")
                state.errors.append(msg)

            try:
                results["news_data"] = future_news.result()
                print(f"[{self.name}]   -> News data fetched successfully.")
            except Exception as e:
                msg = f"News data fetch failed: {e}"
                print(f"[{self.name}] [!] {msg}")
                state.errors.append(msg)

            try:
                results["sec_data"] = future_sec.result()
                print(f"[{self.name}]   -> SEC metadata fetched successfully.")
            except Exception as e:
                msg = f"SEC metadata fetch failed: {e}"
                print(f"[{self.name}] [!] {msg}")
                state.errors.append(msg)
                
            try:
                results["chart_path"] = future_chart.result()
                print(f"[{self.name}]   -> Price chart generated successfully.")
            except Exception as e:
                msg = f"Chart generation failed: {e}"
                print(f"[{self.name}] [!] {msg}")
                state.errors.append(msg)
                
            try:
                results["backtest_chart_path"] = future_backtest.result()
                print(f"[{self.name}]   -> Market backtest chart generated successfully.")
            except Exception as e:
                msg = f"Backtest chart generation failed: {e}"
                print(f"[{self.name}] [!] {msg}")
                state.errors.append(msg)

        # Generate sentiment gauge using news data
        try:
            results["sentiment_chart_path"] = generate_sentiment_gauge(results["news_data"], state.ticker)
            print(f"[{self.name}]   -> Sentiment meter generated successfully.")
        except Exception as e:
            print(f"[{self.name}] [!] Sentiment gauge failed: {e}")

        # After fetching SEC metadata, sequentially extract the 10-K text 
        # (This avoids nested parallel calls that might hit rate limits)
        if results["sec_data"]:
            print(f"[{self.name}] Extracting Item 1A and Item 7 from latest 10-K...")
            for filing in results["sec_data"]:
                if filing.get("form") == "10-K" and "url" in filing:
                    try:
                        raw_text = download_and_clean_html(filing["url"])
                        results["sec_insights"] = extract_10k_items(raw_text)
                        print(f"[{self.name}]   -> 10-K sections extracted successfully.")
                    except Exception as e:
                        msg = f"10-K extraction failed: {e}"
                        print(f"[{self.name}] [!] {msg}")
                        state.errors.append(msg)
                    break
        
        # Populate the shared state
        state.raw_data = results
        print(f"[{self.name}] Data gathering complete.")
        return state

